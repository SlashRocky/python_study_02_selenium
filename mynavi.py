import datetime
import logging
import math
import os
import signal
import sys

from selenium import webdriver
from time import sleep

import pandas as pd


class Scraping(object):
    def __init__(self):

        # ログの出力名を設定
        self.logger = logging.getLogger('LoggingMynavi')

        # ロギングレベルの設定 （DEBUG以上に設定）
        self.logger.setLevel(10)

        # ログのファイル出力先を設定
        self.fh = logging.FileHandler('./logs/mynavi.log')
        self.logger.addHandler(self.fh)

        # ログの出力形式の設定
        self.formatter = logging.Formatter('%(asctime)s:%(lineno)d:%(levelname)s:%(message)s')
        self.fh.setFormatter(self.formatter)

        self.logger.log(20, 'start scraping')
        print('開始します。')
        self.logger.log(20, 'booting...')
        print('\n起動しています・・・')

        # 全ての「会社名」を格納するリスト：company_names
        self.company_names = []
        # 全ての会社の募集要項の詳細情報を格納するリスト：contents
        self.contents = []

    def launch_chrome(self):
        self.browser = webdriver.Chrome()

    def access_site(self):
        self.browser.get('https://tenshoku.mynavi.jp/search/')

        self.logger.log(20, 'loading...')
        print('\nデータをロード中です・・・')

        # 読み込みを待つために５秒間処理を停止
        sleep(5)

        # ポップアップがあれば閉じる
        if self.browser.find_element_by_class_name('karte-close'):
            self.browser.find_element_by_class_name('karte-close').click()
        else:
            pass

    def search_by_keyword(self):

        self.logger.log(20, 'ready')
        print('\n準備が整いました！')

        while True:
            try:
                # キーワード欄にキーワードを入力
                self.elem_keyword_box = self.browser.find_element_by_name('srFreeSearchKeyword')
                self.elem_keyword_box.clear()

                self.logger.log(20, 'enter the keywords you are interested in...')
                self.elem_keyword = input("\n気になるキーワードを入力してください！\n\n")

                self.elem_keyword_box.send_keys(self.elem_keyword)

                # 検索ボタンをクリック
                if self.browser.find_elements_by_class_name('btnPrimaryL'):
                    self.browser.find_element_by_class_name('btnPrimaryL').click()
                else:
                    self.browser.find_element_by_class_name('btnSearch').click()

                # 何件あるかカウント
                self.number_of_cases = int(self.browser.find_element_by_class_name('js__searchRecruit--count').text)

                self.logger.log(20, f'{self.number_of_cases} jobs were found')
                print(f'\n{self.number_of_cases}件の求人情報がヒットしました。')

                # ページ数カウント
                if self.number_of_cases == 0:
                    self.logger.log(20, f'There are no jobs available for {self.elem_keyword}')
                    print(f'{self.elem_keyword}の求人情報はありません。\n')

                elif self.number_of_cases <= 50:
                    self.number_of_pages = 1

                    self.logger.log(20, f'There are {self.number_of_pages} pages')
                    print(f'{self.number_of_pages}ページあります。\n')

                else:
                    self.number_of_pages = math.ceil(self.number_of_cases / 50)

                    self.logger.log(20, f'There are {self.number_of_pages} pages')
                    print(f'{self.number_of_pages}ページあります。\n')

                if self.number_of_cases != 0:
                    break
                else:
                    self.logger.log(20, 'Try searching again with a different keyword.')
                    print('\n別のキーワードで検索しなおしてね。')
            except:
                break

    def check_class_name(self):
        """
        案件により、募集内容詳細が格納されているタグに付与されているクラス名が違うので、それぞれいくつあるか確認する関数
        """
        # クラス名「cassetteRecruitRecommend__main」が付与されている案件の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素
        self.elems_recommend_application_details = self.browser.find_elements_by_class_name('cassetteRecruitRecommend__main')

        # クラス名「cassetteRecruit__main」が付与されている案件の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素
        self.elems_application_details = self.browser.find_elements_by_class_name('cassetteRecruit__main')

        # クラス名「cassetteRecruit__mainM」が付与されている案件の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素
        self.elems_m_application_details = self.browser.find_elements_by_class_name('cassetteRecruit__mainM')

        # クラス名「cassetteRecruit__mainL」が付与されている案件の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素
        self.elems_l_application_details = self.browser.find_elements_by_class_name('cassetteRecruit__mainL')

        # クラス名「cassetteRecruit__mainLL」が付与されている案件の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素
        self.elems_ll_application_details = self.browser.find_elements_by_class_name('cassetteRecruit__mainLL')

    def extract_company_names(self):

        # 「注目」の案件の会社名
        if self.browser.find_elements_by_class_name('cassetteRecruitRecommend__name'):
            self.elems_recommend_company_name = self.browser.find_elements_by_class_name('cassetteRecruitRecommend__name')

            for elem_recommend_company_name in self.elems_recommend_company_name:
                self.recommend_company_name = elem_recommend_company_name.text.split("|")[0].strip()
                self.company_names.append(self.recommend_company_name)

        # 「注目」ではない案件の会社名
        self.elems_company_name = self.browser.find_elements_by_class_name('cassetteRecruit__name')

        for elem_company_name in self.elems_company_name:
            self.company_name = elem_company_name.text.split("|")[0].strip()
            self.company_names.append(self.company_name)

        return self.company_names

    def extract_application_details(self):

        try:
            # クラス名「cassetteRecruitRecommend__main」が付与されている場合
            # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素を取り出す
            for elem_recommend_application_details in self.elems_recommend_application_details:
                self.elems_recommend_application_detail = elem_recommend_application_details.find_elements_by_class_name('tableCondition__body')

                # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の情報を格納するリスト_application_detailsを用意
                _recommend_application_details = []

                # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素をそれぞれひとつずつ取り出して、リストに格納していく
                for elem_recommend_application_detail in self.elems_recommend_application_detail:
                    self.recommend_application_detail = elem_recommend_application_detail.text
                    _recommend_application_details.append(self.recommend_application_detail)

                # 「初年度年収」が記載されてる案件と記載されてない案件があるので、記載されている場合は削除する（揃えたいので）
                if len(_recommend_application_details) > 4:
                    del _recommend_application_details[4]

                # 全ての詳細情報を格納するリストcontentsにappend
                self.contents.append(_recommend_application_details)
        except Exception as e:
            tb = sys.exc_info()[2]
            self.logger.exception('Raise Exception: %s', e.with_traceback(tb))

        try:
            # クラス名「cassetteRecruit__main」が付与されている場合
            # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素を取り出す
            for elem_application_details in self.elems_application_details:
                self.elems_application_detail = elem_application_details.find_elements_by_class_name('tableCondition__body')

                # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の情報を格納するリスト_application_detailsを用意
                _application_details = []

                # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素をそれぞれひとつずつ取り出して、リストに格納していく
                for elem_application_detail in self.elems_application_detail:
                    self.application_detail = elem_application_detail.text
                    _application_details.append(self.application_detail)

                # 「初年度年収」が記載されてる案件と記載されてない案件があるので、記載されている場合は削除する（揃えたいので）
                if len(_application_details) > 4:
                    del _application_details[4]

                # 全ての詳細情報を格納するリストcontentsにappend
                self.contents.append(_application_details)
        except Exception as e:
            tb = sys.exc_info()[2]
            self.logger.exception('Raise Exception: %s', e.with_traceback(tb))

        try:
            # クラス名「cassetteRecruit__mainM」が付与されている場合
            # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素を取り出す
            for elem_m_application_details in self.elems_m_application_details:
                self.elems_m_application_detail = elem_m_application_details.find_elements_by_class_name('tableCondition__body')

                # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の情報を格納するリスト_application_detailsを用意
                _m_application_details = []

                # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素をそれぞれひとつずつ取り出して、リストに格納していく
                for elem_m_application_detail in self.elems_m_application_detail:
                    self.m_application_detail = elem_m_application_detail.text
                    _m_application_details.append(self.m_application_detail)

                # 「初年度年収」が記載されてる案件と記載されてない案件があるので、記載されている場合は削除する（揃えたいので）
                if len(_m_application_details) > 4:
                    del _m_application_details[4]

                # 全ての詳細情報を格納するリストcontentsにappend
                self.contents.append(_m_application_details)
        except Exception as e:
            tb = sys.exc_info()[2]
            self.logger.exception('Raise Exception: %s', e.with_traceback(tb))

        try:
            # クラス名「cassetteRecruit__mainL」が付与されている場合
            # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素を取り出す
            for elem_l_application_details in self.elems_l_application_details:
                self.elems_l_application_detail = elem_l_application_details.find_elements_by_class_name('tableCondition__body')

                # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の情報を格納するリスト_application_detailsを用意
                _l_application_details = []

                # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素をそれぞれひとつずつ取り出して、リストに格納していく
                for elem_l_application_detail in self.elems_l_application_detail:
                    self.l_application_detail = elem_l_application_detail.text
                    _l_application_details.append(self.l_application_detail)

                # 「初年度年収」が記載されてる案件と記載されてない案件があるので、記載されている場合は削除する（揃えたいので）
                if len(_l_application_details) > 4:
                    del _l_application_details[4]

                # 全ての詳細情報を格納するリストcontentsにappend
                self.contents.append(_l_application_details)
        except Exception as e:
            tb = sys.exc_info()[2]
            self.logger.exception('Raise Exception: %s', e.with_traceback(tb))

        try:
            # クラス名「cassetteRecruit__mainLL」が付与されている場合
            # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素を取り出す
            for elem_ll_application_details in self.elems_ll_application_details:
                self.elems_ll_application_detail = elem_ll_application_details.find_elements_by_class_name('tableCondition__body')

                # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の情報を格納するリスト_application_detailsを用意
                _ll_application_details = []

                # 1社分の「仕事内容」、「対象となる方」、「勤務地」、「給与」の要素をそれぞれひとつずつ取り出して、リストに格納していく
                for elem_ll_application_detail in self.elems_ll_application_detail:
                    self.ll_application_detail = elem_ll_application_detail.text
                    _ll_application_details.append(self.ll_application_detail)

                # 「初年度年収」が記載されてる案件と記載されてない案件があるので、記載されている場合は削除する（揃えたいので）
                if len(_ll_application_details) > 4:
                    del _ll_application_details[4]

                # 全ての詳細情報を格納するリストcontentsにappend
                self.contents.append(_ll_application_details)
        except Exception as e:
            tb = sys.exc_info()[2]
            self.logger.exception('Raise Exception: %s', e.with_traceback(tb))

        return self.contents

    def transition_page(self):
        if self.number_of_pages == 1:
            self.logger.log(20, 'getting information...')
            print('情報を取得中です・・・')

            self.check_class_name()
            self.extract_company_names()
            self.extract_application_details()
        else:
            for page in range(1, self.number_of_pages + 1):
                self.url = f'https://tenshoku.mynavi.jp/list/kw{self.elem_keyword}/pg{page}/?jobsearchType=4&searchType=8'
                self.browser.get(self.url)

                self.logger.log(20, f'getting information for page {page} now...')
                print(f'{page}ページ目の情報を取得中です・・・')

                self.check_class_name()
                self.extract_company_names()
                self.extract_application_details()

    def output_search_results_to_csv(self):

        self.df_company_name = pd.DataFrame()
        self.df_company_name['会社名'] = self.company_names

        self.df_contents = pd.DataFrame(self.contents)
        self.df_contents.columns = ['仕事内容', '対象となる方', '勤務地', '給与']

        self.df = pd.concat([self.df_company_name, self.df_contents], axis=1)

        now = datetime.datetime.now()
        self.time = now.strftime('%Y_%m%d_%H%M')

        self.df.to_csv(f'./results/mynavi_search_results_by_{self.elem_keyword}_{self.time}.csv', index=False)

    def send_exit_signal(self):
        os.kill(self.browser.service.process.pid, signal.SIGTERM)

    def __del__(self):
        self.logger.log(20, 'done')
        print('\n完了しました。')


if __name__ == '__main__':
    scraping = Scraping()
    try:
        scraping.launch_chrome()
        scraping.access_site()
        scraping.search_by_keyword()
        scraping.transition_page()
        scraping.output_search_results_to_csv()
    finally:
        scraping.send_exit_signal()
    del scraping
