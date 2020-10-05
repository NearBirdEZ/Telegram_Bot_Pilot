from bs4 import BeautifulSoup  # pip install bs4
from CONFIG import LOGIN, PASSWORD
import re
import requests  # pip install request


class Parser_NM:

    def __create_session(self):
        """Создаем сессию для дальнейшего поиска запроса"""
        URL = 'http://sdn.pilot.ru:8080/fx/$sd/ru.naumen.sd.ui.login_jsp?backUrl=http%3A%2F%2Fsdn.pilot.ru%3A8080%2F' \
              'fx%2Fsd%2Fru.naumen.sd.published_jsp%3Fuuid%3Dcorebofs000080000ikhm8pnur5l85oc'
        auth_dict = {
            'login': LOGIN,
            'password': PASSWORD
        }
        self.session.post(URL, data=auth_dict)

    def __get_html(self, request):
        """Получаем html код запроса для дальнейшего поиска информации на нем"""
        headers = {
            'Upgrade-Insecure-Requests': '1',
            'Host': 'sdn.pilot.ru:8080'
        }

        data = {
            'sdsearch_ServiceCallIdSearchType': None,
            'hidden_dosearchsdsearch_ServiceCallIdSearchType': '1',
            'searchType__exists': '1',
            'searchInResult__exists': '1',
            '__form_id': 'searchTab.searchForm',
            'first_load': 'true'
        }
        """Заносим информацию в словарь для поиска"""
        data.update({'sdsearch_ServiceCallIdSearchType': f'{request}'})
        """URL адрес, куда направляется POST запрос"""
        request_url = 'http://sdn.pilot.ru:8080/fx/$sd/servlet.ru.naumen.sd.search.SearcherServlet'
        html = self.session.post(request_url, headers=headers, data=data)
        return html

    def __get_html_task(self, html):
        """Получение страницы, на которой отражены все задачи по запросу"""
        html_task = self.session.get(html.url + '&activeComponent=Tasks')
        return html_task

    def __get_bonds(self, html):
        """Получение страницы, на которой отражены связаныне заявки"""
        html_bond = self.session.get(html.url + '&activeComponent=Relationship')
        return html_bond

    def __resub(self, info):
        """Удалем из переданной в запрос информации (описание запроса и задачи) лишнюю информацию:
        1. Номера телефонов
        2. Номера ККТ
        3. Пин-коды магазинов, к сожалению, затрагивает и номера запросов (в описании),например, Алькоровских.
        4. Разного рода e-mail адреса
        5. Все ссылки на сайты"""
        info = re.sub(
            r'((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}\b|'  # номер телефона/номера ккт/номера запрососов в описании
            r'([a-zA-Z0-9_-]+\.)*[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)*\.[a-z]{2,6}\b|'  # электронная почта
            r'([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3}):?\d{0,5}|'  # ip-адрес
            r'(http://)?(https://)?(www)?\.?[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)*\.[a-zA-Z]{2,6}\b',  # сайты
            '(информация скрыта)', info)
        return info

    def __get_content(self, html, flag):
        """Парсинг переданной страницы
        Имеется 3 флага:
        flag = 1: Парсинг страницы запроса
        flag = 2: Парсинг страницы с задачами
        flag = 3: Парсинг страницы со связанным заявками"""
        soup = BeautifulSoup(html.text, 'html.parser')
        if flag == 1:
            description = soup.find('td', class_='servicecall_description_inner').get_text().split('Описание запроса')[
                1].strip()
            rep = ['<', '>', '  ']
            for r in rep:
                description = description.replace(r, ' ')
            description = description.replace('\n\n', '\n')
            description = self.__resub(description)
            time_send_request = soup.find(
                'td',
                {'id': 'ServiceCall.Container.Column_1.ServiceCallProps.request_date'}
            ).get_text().strip()
            address_store = soup.find('td',
                                      {'id': 'ServiceCall.Container.Column_2.CustomerProps.client'}).get_text().strip()
            status = soup.find('td',
                               {
                                   'id': 'ServiceCall.Container.Column_1.ServiceCallProps.current_status'}).get_text().strip()
            responsible = soup.find('td',
                                    {
                                        'id': 'ServiceCall.Container.Column_1.ServiceCallProps.responsible'}).get_text().strip()
            type_req = soup.find('td',
                                 {
                                     'id': 'ServiceCall.Container.Column_1.ServiceCallProps.servicecall_case'}).get_text().strip()
            contract = soup.find('td',
                                 {
                                     'id': 'ServiceCall.Container.Column_2.CustomerProps.contract_id'}).get_text().strip().lower().split()
            email = soup.find('td',
                              {
                                  'id': 'ServiceCall.Container.Column_2.CustomerProps.client_email'}).get_text().strip().lower().split(
                '@')
            service_id = soup.find('td',
                                   {
                                       'id': 'ServiceCall.Container.Column_2.CustomerProps.service_id'}).get_text().strip().lower().split()
            """Возвращается кортеж со значениями:
            0 - описание
            1 - время обращения
            2 - адрес магазина
            3 - тип запроса (служебная информация)
            4 - статус заявки, 
            5 - ответственные
            6 - договор (служебная информация)
            7 - email(служебная информация)
            8 - услуга (служебная информация)"""
            return description, time_send_request, address_store, type_req, status, responsible, contract, email, service_id
        elif flag == 2:
            # задачи
            task = soup.find('table', {
                'id': 'Tasks.Tasks.TasksActionContainer.ObjectListReport.tableListAndButtons.Taskstasklist_report'}).get_text().split(
                '\n')
            tasks = []
            for i in range(len(task)):
                if (i + 1) % 53 == 0 and i != 52:
                    tmp = self.__resub(task[i].strip())
                    tasks.append(tmp)
            return tasks
        elif flag == 3:
            # связанные заявки
            bond = soup.find('table', {
                'id': 'Relationship.relations_container.container.LeftRelatedServiceCallsList'}).get_text().split()
            bonds = [x for x in bond if x.isdigit()]
            return bonds

    def get_content(self, request):
        """Некое подобие мейна в классе, который собирает в себе все функции и возвращает информацию,
        относительно их содержимого"""

        """Объявление сессии"""
        self.session = requests.Session()
        self.__create_session()

        """Получение страницы запроса"""
        html_index = self.__get_html(request)

        """Если статус запроса вернул 200, продолжаем парсить, иначе Naumen на профилактике/выключен"""
        if html_index.ok:
            html_bonds = self.__get_bonds(html_index)
            html_tasks = self.__get_html_task(html_index)
            self.session.close()

            """Получаем значения со страниц"""
            content_index = self.__get_content(html_index, 1)
            content_tasks = self.__get_content(html_tasks, 2)
            content_bonds = self.__get_content(html_bonds, 3)

            """Для удобного чтения задач разделяем их между собой на \n\n"""
            if len(content_tasks) > 0:
                content_tasks = '\n\n'.join(content_tasks)
            else:
                content_tasks = 'Работы не проводились'

            if len(content_bonds) < 1:
                content_bonds = ['Отсутствуют']

            check = [word.lower() for word in
                     (content_index[2].lower().split() + content_index[6] + content_index[7] + content_index[8])]

            """Провека на доступ к запросам извне
            1. Не должно быть перепиской
            2. Не служебный контрагент - Пилот Москва
            3. Не обработанная заявка с контрагентом Pilot (может быть первым пунктом или информацией от исполнителя, 
            которая не затрагивает заказчика)
            4. Не должен быть служебным магазином IDB 3000
            5. Не должен содержать слово тест или профилактика в контрагенте/e-mail/услуге"""
            if content_index[3] != 'Переписка' and \
                    content_index[2] not in ['Пилот Москва', 'Pilot', 'Иль де Ботэ 3000 временный'] and \
                    'тест' not in check and \
                    'test' not in check and \
                    'профилактика' not in check:
                return f'''Описание запроса № {request}
{content_index[0]}
{'-' * 40}
Статус обращения
{content_index[4]}
{'-' * 40}
Ответственный отдел
{content_index[5]}
{'-' * 40}
Время обращения
{content_index[1]}
{'-' * 40}
Связанные заявки
{", ".join(content_bonds)}
{'-' * 40}
Выполненые работы
{content_tasks}
{'-' * 40}
'''
            else:
                return 'Отказано в доступе.'
        else:
            return 'Сервер временно не доступен, попробуйте через 5 минут'


if __name__ == '__main__':
    pass
