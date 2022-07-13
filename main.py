import re
import roman
# import timeit
from bs4 import BeautifulSoup,Doctype
from os.path import exists

class UnstructuredHtmlToStructuredHtml:
    def __init__(self):
        self.html_file = None
        self.soup= None
        self.dictionary_to_store_part = {}
        self.list_of_section = []
        self.part_section=[]
        self.dictionary_to_store_class_name = {'h1': r'^Title \d+', 'h4': 'Compiler’s Notes\.',
                                               'History': 'History of Section\.',
                                               'li': r'^Chapters? \d+(.\d+)?(.\d+)?',
                                               'h3': r'^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?',
                                               'h2': r'^Chapters? \d+(.\d+)?(.\d+)?',
                                               'junk': 'Text', 'ol_of_i': '\([A-Z a-z]\)'}

    def create_soup(self, file_name):
        self.html_file = file_name
        file_name = open(html_file)
        self.soup = BeautifulSoup(file_name, 'html.parser')
        self.soup.contents[0].replace_with(Doctype("html"))
        self.soup.html.attrs['lang'] = 'en'
        file_name.close()

    def get_class_name(self):
        for key in self.dictionary_to_store_class_name:
            # print(help(self.soup.find))
            # print(timeit.timeit(self.soup.find(
            #     lambda tag: tag.name == 'p' and re.search(self.dictionary_to_store_class_name[key], tag.text.strip())
            #                 and tag.attrs['class'][0] not in
            #                 self.dictionary_to_store_class_name.values())))
            tag_class = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(self.dictionary_to_store_class_name[key], tag.text.strip())
                            and tag.attrs['class'][0] not in
                            self.dictionary_to_store_class_name.values())
            if tag_class:
                class_name = tag_class['class'][0]
                self.dictionary_to_store_class_name[key] = class_name
        print(self.dictionary_to_store_class_name)
    # def get_class_name(self):
    #     def class_name(tag):
    #         return tag.name=="p" and re.search(self.dictionary_to_store_class_name[key], tag.text.strip()) and \
    #                     tag.attrs['class'][0] not in self.dictionary_to_store_class_name.values()
    #
    #     for key in self.dictionary_to_store_class_name:
    #         # print(timeit.timeit(self.soup.find(class_name)))
    #         tag_class = self.soup.find(class_name)
    #         if tag_class:
    #             classname = tag_class['class'][0]
    #             self.dictionary_to_store_class_name[key] = classname
    #     print(self.dictionary_to_store_class_name)

    def remove_junk(self):
        for tag in self.soup.find_all("p", string=re.compile('Annotations|Text|History')):
            class_name = tag['class'][0]
            if class_name == self.dictionary_to_store_class_name['junk']:
                tag.decompose()

    def convert_to_header_and_assign_id(self):
        list_to_store_regex_for_h4 = ['Compiler’s Notes.', 'Compiler\'s Notes.', 'Cross References.',
                                      'Comparative Legislation.',
                                      'Collateral References.', 'NOTES TO DECISIONS',
                                      'Repealed Sections.', 'Effective Dates.', 'Law Reviews.', 'Rules of Court.']
        count_for_duplicate = 0
        for tag in self.soup.find_all("p"):
            class_name = tag['class'][0]
            if class_name == self.dictionary_to_store_class_name['h1']:
                tag.name = "h1"
                if re.search("^Title \d+", tag.text):
                    title_number = re.search("^Title (?P<title_number>\d+)", tag.text).group('title_number').zfill(2)
                    tag.attrs['id'] = f"t{title_number}"
                else:
                    raise Exception('Title Not found...')
            elif class_name == self.dictionary_to_store_class_name['h2']:
                if re.search("^Chapters? \d+(.\d+)?(.\d+)?", tag.text):
                    tag.name = "h2"
                    chapter_number = re.search("^Chapters? (?P<chapter_number>\d+(.\d+)?(.\d+)?)", tag.text).group(
                        'chapter_number').zfill(2)
                    tag.attrs['id'] = f"{tag.find_previous_sibling('h1').attrs['id']}c{chapter_number}"
                    tag.attrs['class'] = "chapter"
                elif re.search("^Part \d{1,2}", tag.text):
                    self.list_of_section=[]
                    tag.name = "h2"
                    part_number = re.search("^Part (?P<part_number>\d{1,2})", tag.text).group('part_number').zfill(2)
                    tag.attrs['id'] = f"{tag.find_previous_sibling('h2', class_='chapter').attrs['id']}p{part_number}"
                else:
                    raise Exception('header2 pattern Not found...')
            elif class_name == self.dictionary_to_store_class_name['h3']:
                tag.name = "h3"
                tag['class'] = "section"
                if re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?", tag.text.strip()):
                    id_of_section = re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?", tag.text.strip()).group()
                    section_id = f"{tag.find_previous_sibling('h2').attrs['id']}s{id_of_section}"
                    if re.search('^Part \d{1,2}',tag.find_previous_sibling('h2').text.strip()):
                        part_id=re.search('c\d+p\d+',tag.find_previous_sibling('h2').attrs['id']).group()
                        self.list_of_section.append(id_of_section)
                        self.part_section.append(id_of_section)
                        self.dictionary_to_store_part[f"{part_id.zfill(2)}"] = list(set(self.list_of_section))
                    duplicate = self.soup.find_all("h3", id=section_id)
                    if len(duplicate):  # 4-1.1-1
                        count_for_duplicate += 1
                        tag.attrs['id'] = f"{section_id}.{str(count_for_duplicate).zfill(2)}"
                    else:
                        count_for_duplicate = 0
                        tag.attrs['id'] = section_id
                else:
                    raise Exception('section pattern not found...')

            elif class_name == self.dictionary_to_store_class_name['h4']:
                if tag.text.strip() in list_to_store_regex_for_h4:
                    tag.name = "h4"
                    if tag.find_previous_sibling().attrs['class'][0] == self.dictionary_to_store_class_name['li']:  # t3c13repealed section
                        tag.attrs['id'] = f"{tag.find_previous_sibling('h2').attrs['id']}-{re.sub(r'[^a-zA-Z0-9]', '', tag.text).lower()}"
                    else:
                        tag.attrs['id'] = f"{tag.find_previous_sibling('h3').attrs['id']}-{re.sub(r'[^a-zA-Z0-9]', '', tag.text).lower()}"
                if tag.text.strip() == 'NOTES TO DECISIONS':
                    tag_id = tag.attrs['id']
                    for sub_tag in tag.find_next_siblings():
                        class_name = sub_tag.attrs['class'][0]
                        if class_name == self.dictionary_to_store_class_name['History']:
                            sub_tag.name = 'li'
                        elif class_name == self.dictionary_to_store_class_name['h4'] and sub_tag.b and re.search('Collateral References\.', sub_tag.text) is None:
                            sub_tag.name = "h5"
                            sub_tag_id = re.sub(r'[^a-zA-Z0-9]', '', sub_tag.text).lower()
                            if re.search('^—.*', sub_tag.text):
                                sub_tag.attrs['id'] = f"{sub_tag.find_previous_sibling('h5', class_='notes_section').attrs['id']}-{sub_tag_id}"
                            else:
                                sub_tag.attrs['id'] = f"{tag_id}-{sub_tag_id}"
                                sub_tag.attrs['class'] = 'notes_section'
                        elif re.search('^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?', sub_tag.text) or re.search('Collateral References\.', sub_tag.text) or re.search('^Part \d{1,2}',sub_tag.text) or re.search('^Chapters? \d+(.\d+)?(.\d+)?', sub_tag.text):
                            break
            elif class_name == self.dictionary_to_store_class_name['History']:
                if re.search("^History of Section\.", tag.text):
                    h4_tag = self.soup.new_tag("h4")
                    h4_tag.string = "History of Section."
                    tag.insert_before(h4_tag)
                    tag.string = re.sub('History of Section.', '', tag.text)
                    sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', h4_tag.text).lower()
                    if h4_tag.find_previous_sibling().attrs['class'] == "nav_li":  # history of section
                        h4_tag.attrs['id'] = f"{h4_tag.find_previous_sibling('h2').attrs['id']}-{sub_section_id}"
                    else:
                        h4_tag.attrs['id'] = f"{h4_tag.find_previous_sibling('h3').attrs['id']}-{sub_section_id}"
                elif re.search("^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})", tag.text.strip(), re.IGNORECASE):
                    tag.name = "h3"
                    article_id = re.search("^ARTICLE (?P<article_id>(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))",tag.text.strip(), re.IGNORECASE).group('article_id')
                    tag['id'] = f"{tag.find_previous_sibling('h3', class_='section').attrs['id']}a{article_id}"
                elif re.search("^Section \d+. [a-z ,\-A-Z]+\. \(a\)", tag.text.strip()) and re.search("^\(b\)",tag.find_next_sibling().text.strip()):  # section 14
                    text_from_b = tag.text.split('(a)')
                    p_tag_for_section = self.soup.new_tag("p")
                    p_tag_for_section.string = text_from_b[0]
                    p_tag_for_a = self.soup.new_tag("p")
                    p_tag_text = f"(a){text_from_b[1]}"
                    p_tag_for_a.string = p_tag_text
                    tag.insert_before(p_tag_for_section)
                    tag.insert_before(p_tag_for_a)
                    p_tag_for_a.attrs['class'] = [self.dictionary_to_store_class_name['History']]
                    p_tag_for_section.attrs['class'] = [self.dictionary_to_store_class_name['History']]
                    tag.decompose()
            elif class_name == self.dictionary_to_store_class_name['li']:
                if re.search("^Chapters? \d+(.\d+)?(.\d+)?", tag.text.strip()) or re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?", tag.text.strip()) or re.search('^Part \d{1,2}',tag.text.strip()):
                    tag.name = "li"
                    tag['class'] = "nav_li"

    def create_li_with_anchor(self, li_tag, id, li_type=None, li_count=None):
        li_tag_text = li_tag.text
        li_tag.clear()
        li_tag.append(self.soup.new_tag("a", href='#' + id))
        li_tag.a.string = li_tag_text
        if li_type:
            li_tag['id'] = f"{id}-{li_type}{str(li_count).zfill(2)}"
        return li_tag

    def create_nav_and_ul_tag(self):
        ul_tag_for_chapter = self.soup.new_tag("ul")
        ul_tag_for_section = self.soup.new_tag("ul")
        ul_tag_for_header5 = self.soup.new_tag("ul")
        ul_tag_for_sub_section = self.soup.new_tag("ul")
        ul_tag_for_part = self.soup.new_tag("ul")
        li_count_for_chapter = 0
        li_count_for_section = 0
        li_count_for_part = 0
        count_for_duplicate = 0
        for li_tag in self.soup.find_all("li"):
            if re.search("^Chapters? \d+(.\d+)?(.\d+)?", li_tag.text.strip()):
                if re.search("^Chapters? (?P<chapter_number>\d+(.\d+)?(.\d+)?)", li_tag.text.strip()):
                    chapter_number = re.search("^Chapters? (?P<chapter_number>\d+(.\d+)?(.\d+)?)", li_tag.text.strip()).group(
                        'chapter_number').zfill(2)
                    h1_id = f"{li_tag.find_previous_sibling('h1').attrs['id']}c{chapter_number}"
                    li_count_for_chapter += 1
                    li_tag = self.create_li_with_anchor(li_tag, h1_id, "cnav", li_count_for_chapter)
                    ul_tag_for_chapter.attrs['class'] = 'leaders'
                    li_tag.wrap(ul_tag_for_chapter)
                else:
                    raise Exception('chapter li pattern not found')
            elif re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?", li_tag.text.strip()):
                nav_tag_for_section_ul = self.soup.new_tag("nav")
                if re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?", li_tag.text.strip()):
                    section_id = re.search("^\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?", li_tag.text.strip()).group()
                    h3_id = f"{li_tag.find_previous_sibling('h2').attrs['id']}s{section_id}"
                    duplicate = self.soup.find_all("a", href='#' + h3_id)
                    if len(duplicate):
                        count_for_duplicate += 1
                        id_count = str(count_for_duplicate).zfill(2)
                        h3_id = f"{h3_id}.{id_count}"
                    else:
                        count_for_duplicate = 0
                    li_count_for_section += 1
                    li_tag = self.create_li_with_anchor(li_tag, h3_id, "snav", li_count_for_section)
                    next_tag = li_tag.find_next_sibling()
                    ul_tag_for_section.attrs['class'] = 'leaders'
                    if next_tag.name == "h3" or next_tag.name == "h4":
                        li_tag.wrap(ul_tag_for_section)
                        ul_tag_for_section.wrap(nav_tag_for_section_ul)
                        ul_tag_for_section = self.soup.new_tag("ul")
                        nav_tag_for_section_ul = self.soup.new_tag("nav")
                        li_count_for_section = 0
                    else:
                        li_tag.wrap(ul_tag_for_section)
                else:
                    raise Exception('section li pattern not found')
            elif re.search("^Part \d{1,2}", li_tag.text.strip()):
                nav_tag_for_part_ul = self.soup.new_tag("nav")
                if re.search("^Part \d{1,2}", li_tag.text.strip()):
                    part_id = re.search("^Part (?P<part_number>\d{1,2})", li_tag.text.strip()).group('part_number').zfill(2)
                    h2_id = li_tag.find_previous_sibling('h2').attrs['id']
                    li_count_for_part += 1
                    li_tag = self.create_li_with_anchor(li_tag, f"{h2_id}p{part_id}", "snav", li_count_for_part)
                    next_tag = li_tag.find_next_sibling()
                    ul_tag_for_part.attrs['class'] = 'leaders'
                    if next_tag.name == "h2":
                        li_tag.wrap(ul_tag_for_part)
                        ul_tag_for_part.wrap(nav_tag_for_part_ul)
                        ul_tag_for_part = self.soup.new_tag("ul")
                        nav_tag_for_part_ul = self.soup.new_tag("nav")
                        li_count_for_part = 0
                    else:
                        li_tag.wrap(ul_tag_for_part)
                else:
                    raise Exception('part li pattern not found')

            else:
                ul_tag_for_sub_section.attrs['class'] = 'leaders'
                ul_tag_for_header5.attrs['class'] = 'leaders'
                h4_id = li_tag.find_previous_sibling("h4").attrs['id']
                sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', li_tag.text.strip()).lower()
                if re.search('^—.*', li_tag.text.strip()):
                    id_of_parent = re.sub(r'[^a-zA-Z0-9]', '',
                                          li_tag.find_previous_sibling().find_all("li", class_="notes_to_decision")[
                                              -1].text).lower()
                    h5_id = f"{h4_id}-{id_of_parent}-{sub_section_id}"
                    li_tag = self.create_li_with_anchor(li_tag, h5_id)
                    if re.search('^—.*', li_tag.find_next_sibling().text.strip()):
                        li_tag.wrap(ul_tag_for_sub_section)
                        ul_tag_for_header5.append(ul_tag_for_sub_section)
                    elif li_tag.find_next_sibling().name == "h5":
                        li_tag.wrap(ul_tag_for_sub_section)
                        ul_tag_for_header5.find_all("li")[-1].append(ul_tag_for_sub_section)
                        ul_tag_for_sub_section = self.soup.new_tag("ul")
                        ul_tag_for_header5.wrap(nav_tag_for_notes_to_decision_ul)
                        ul_tag_for_header5 = self.soup.new_tag("ul")
                    else:
                        li_tag.wrap(ul_tag_for_sub_section)
                        ul_tag_for_header5.find_all("li")[-1].append(ul_tag_for_sub_section)
                        ul_tag_for_sub_section = self.soup.new_tag("ul")
                else:
                    h5_id = f"{h4_id}-{sub_section_id}"
                    self.create_li_with_anchor(li_tag, h5_id)
                    li_tag['class'] = 'notes_to_decision'
                    nav_tag_for_notes_to_decision_ul = self.soup.new_tag("nav")
                    if li_tag.find_next_sibling().name == "h5":
                        li_tag.wrap(ul_tag_for_header5)
                        ul_tag_for_header5.wrap(nav_tag_for_notes_to_decision_ul)
                        ul_tag_for_header5 = self.soup.new_tag("ul")
                        nav_tag_for_notes_to_decision_ul = self.soup.new_tag("nav")
                    else:
                        li_tag.wrap(ul_tag_for_header5)

    def create_nav_and_main_tag(self):
        nav_tag_for_header1_and_chapter = self.soup.new_tag("nav")
        p_tag=self.soup.new_tag("p")
        p_tag['class']="transformation"
        p_tag.string="Release 70 of the Official Code of Rhode Island Annotated released 2021.11. Transformed and posted by Public.Resource.Org using rtf-parser.py version 1.0 on 2022-06-13. This document is not subject to copyright and is in the public domain."
        nav_tag_for_header1_and_chapter.append(p_tag)
        main_tag = self.soup.new_tag("main")
        self.soup.find("h1").wrap(nav_tag_for_header1_and_chapter)
        self.soup.find("ul").wrap(nav_tag_for_header1_and_chapter)
        for tag in nav_tag_for_header1_and_chapter.find_next_siblings():
            tag.wrap(main_tag)

    def add_citation(self):
        for tag in self.soup.find_all(["p", "li"]):
            tag_string = ''
            text = str(tag)
            text = re.sub('^<p[^>]*>|</p>$', '', text.strip())
            cite_tag_pattern = {
                'alr_pattern': '\d+ A.(L.R.)?( Fed. )?(\d[a-z]{1,2})?( Art.)? ?\d+',
                'pl_pattern': '(impl\. am\. )?P\.L\. \d+',
                'gl_pattern': '(G\.L\. ?\d+)',
                'us_ammend': 'U\.S\. Const\., Amend\. (\d+|(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.)( C)?',
                'sct': '(\d+ S\. Ct\. \d+)',
                'led': '(\d+ L\. Ed\. \d+[a-z] \d+)',
                'ann_laws': '(Ann\. Laws ch\. \d+)',
                'ri': '(\d+ R\.I\. \d+)',
                'ri_lexis': '(\d+ R\.I\. LEXIS \d+)',
                'us': '(\d+ U\.S\. \d+)',
                'us_lexis': '(\d+ U\.S\. LEXIS \d+)',
                'a_2d': '(\d+ A\.2d \d+)',
                'roger': '\d+ R(\.|oger )W(\.|illiams )U\. ?L\. Rev. \d+',
                'cfr': '(\d+ CFR \d+\.\d+(?!\d+-))',
                'usc':'(\d+ U\.S\.C\.)',
                'supp': '(\d+ F\. Supp\. \d+)',
                'us_dist_lexis': '(U\.S\. Dist\. LEXIS \d+)'
            }
            for key in cite_tag_pattern:
                cite_pattern = cite_tag_pattern[key]
                if re.search(cite_pattern, tag.text.strip()) and tag.attrs['class'] != "nav_li":
                    for cite_pattern in set(match[0] for match in re.findall('(' + cite_tag_pattern[key] + ')', tag.text.strip())):
                        tag_string = re.sub(cite_pattern, f"<cite>{cite_pattern}</cite>", text)
                        text = tag_string

            if re.search('\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?((\([a-z 0-9 (ix|iv|v?i{0,3}) A-Z]\))+)?', tag.text.strip()) and tag.attrs['class'] != "nav_li":
                for pattern in sorted(set(match[0] for match in re.findall('(\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?((\([a-z 0-9 (ix|iv|v?i{0,3}) A-Z]\))+)?)', tag.text.strip()))):
                    section_match = re.search("(?P<section_id>(?P<title_id>\d+)-(?P<chapter_id>\d+)((-\d+)?(\.\d+(-\d+)?(\.\d+)?)?))",pattern)
                    file_exists = exists(f'/home/mis/PycharmProjects/practice/venv/ricode/modified/gov.ri.code.title.{section_match.group("title_id").zfill(2)}.html')
                    if file_exists:
                        file=open(f'/home/mis/PycharmProjects/practice/venv/ricode/modified/gov.ri.code.title.{section_match.group("title_id").zfill(2)}.html')
                        content=file.read()
                        file.close()
                    else:
                        continue
                    if re.search('\d+-\d+-\d+\.\d+', pattern):
                        if re.search(f'id="(?P<tag_id>(.+s{pattern}))"',content):
                            tag_id=re.search(f'id="(?P<tag_id>(.+s{pattern}))"',content).group('tag_id')
                            tag_string = re.sub(pattern, f"<cite><a href=http://localhost:63342/practice/venv/ricode/modified/gov.ri.code.title.{section_match.group('title_id').zfill(2)}.html?_ijt=lartillgujbilc2c7ak6tlmhr8&_ij_reload=RELOAD_ON_SAVE#{tag_id} target='_self'>{pattern}</a></cite>", text)
                            text = tag_string
                    elif re.search(f'\d+-\d+(-\d+)?(\.\d+(-\d+)?(\.\d+)?)?(\([a-z 0-9 (ix|iv|v?i{0,3}) A-Z]\))+',pattern):
                        match=re.search(f'(\([a-z 0-9 (ix|iv|v?i{0,3}) A-Z]\))+',pattern).group()
                        match=match.replace('(','').replace(')','')
                        print(match)
                        # alpha_id=section_match.group('li_alpha')
                        # number_id=section_match.group('li_num')
                        section_id=section_match.group('section_id')
                        if re.search(f'id=".+s{section_id}ol1{match}"',content):
                            tag_id=re.search(f'id="(?P<tag_id>(.+s{section_id}ol1{match}))"',content).group('tag_id')
                            tag_string = re.sub(fr'{re.escape(pattern)}', f"<cite><a href=http://localhost:63342/practice/venv/ricode/modified/gov.ri.code.title.{section_match.group('title_id').zfill(2)}.html?_ijt=lartillgujbilc2c7ak6tlmhr8&_ij_reload=RELOAD_ON_SAVE#{tag_id} target='_self'>{pattern}</a></cite>", text)
                        text = tag_string
                    else:
                        if re.search('(?<!\.|-)\d+-\d+(?!((\d)?\.\d+)|((\d)?-\d+))', pattern):#12-32
                            chapter_id=section_match.group('chapter_id').zfill(2)
                            if re.search(f'id=".+c{chapter_id}"',content):
                                tag_id = re.search(f'id="(?P<tag_id>(.+c{chapter_id}))"', content).group('tag_id')
                                tag_string = re.sub(pattern,f"<cite><a href=http://localhost:63342/practice/venv/ricode/modified/gov.ri.code.title.{section_match.group('title_id').zfill(2)}.html?_ijt=lartillgujbilc2c7ak6tlmhr8&_ij_reload=RELOAD_ON_SAVE#{tag_id} target='_self'>{pattern}</a></cite>",text)
                        else:
                            if re.search('\d+-\d+-\d', pattern):
                                if re.search(f'id=".+s{pattern}"' ,content):
                                    tag_id = re.search(f'id="(?P<tag_id>(.+s{pattern}))"', content).group('tag_id')
                                    tag_string = re.sub(pattern + '(?!((\d)?\.\d+)|(\d+))',f"<cite><a href=http://localhost:63342/practice/venv/ricode/modified/gov.ri.code.title.{section_match.group('title_id').zfill(2)}.html?_ijt=lartillgujbilc2c7ak6tlmhr8&_ij_reload=RELOAD_ON_SAVE#{tag_id} target='_self'>{pattern}</a></cite>",text)
                            elif re.search('\d+-\d+-\d+', pattern):
                                if re.search(f'id=".+s{pattern}"', content):
                                    tag_id = re.search(f'id="(?P<tag_id>(.+s{pattern}))"', content).group('tag_id')
                                    tag_string = re.sub(pattern + '(?!((\d)?\.\d+))',f"<cite><a href=http://localhost:63342/practice/venv/ricode/modified/gov.ri.code.title.{section_match.group('title_id').zfill(2)}.html?_ijt=lartillgujbilc2c7ak6tlmhr8&_ij_reload=RELOAD_ON_SAVE#{tag_id} target='_self'>{pattern}</a></cite>",text)
                            elif re.search('\d+-\d+\.\d+-\d+(\.\d+)?', pattern):
                                if re.search(f'id=".+s{pattern}"', content):
                                    tag_id = re.search(f'id="(?P<tag_id>(.+s{pattern}))"', content).group('tag_id')
                                    tag_string = re.sub(pattern,f"<cite><a href=http://localhost:63342/practice/venv/ricode/modified/gov.ri.code.title.{section_match.group('title_id').zfill(2)}.html?_ijt=lartillgujbilc2c7ak6tlmhr8&_ij_reload=RELOAD_ON_SAVE#{tag_id} target='_self'>{pattern}</a></cite>",text)
                        text = tag_string
            if tag_string:
                tag.clear()
                tag.append(BeautifulSoup(tag_string, features="html.parser"))

    def create_ol_tag(self):
        alphabet = 'a'
        number = 1
        roman_number = 'i'
        inner_roman = 'i'
        caps_alpha = 'A'
        inner_num = 1
        caps_roman = 'I'
        inner_alphabet = 'a'
        ol_count = 1
        ol_tag_for_roman = self.soup.new_tag("ol", type='i')
        ol_tag_for_number = self.soup.new_tag("ol")
        ol_tag_for_alphabet = self.soup.new_tag("ol", type='a')
        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
        ol_tag_for_inner_number = self.soup.new_tag("ol")
        ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
        ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
        count_of_p_tag = 1
        for tag in self.soup.main.find_all("p"):
            if not tag.name:
                continue
            class_name = tag['class'][0]
            if class_name == self.dictionary_to_store_class_name['History'] or class_name == self.dictionary_to_store_class_name['ol_of_i']:
                if re.search("^[a-z A-Z]+", tag.text):
                    next_sibling = tag.find_next_sibling()
                    if next_sibling and tag.name == "h3":
                        ol_count = 1
                if tag.i:
                    tag.i.unwrap()
                next_tag = tag.find_next_sibling()
                if not next_tag:  # last tag
                    break
                if next_tag.next_element.name and next_tag.next_element.name == 'br':
                    next_tag.decompose()
                    next_tag = tag.find_next_sibling()
                if next_tag.name != 'h4':
                    if re.search('^\(\d{1,2}\) \((ix|iv|v?i{0,3})\) \([A-Z]\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        ol_id_of_number = re.search('^\((?P<ol_id_number>\d{1,2})\)', tag.text.strip()).group('ol_id_number')
                        ol_id_of_roman = re.search('\((?P<ol_id_roman>(ix|iv|v?i{0,3}))\)', tag.text.strip()).group('ol_id_roman')
                        alphabet_id = re.search('\((?P<alphabet_id>[A-Z])\)', tag.text.strip()).group('alphabet_id')
                        tag_string = re.sub('^<li[^>]*>(<span.*</span>)?<b>\(\d{1,2}\) \((ix|iv|v?i{0,3})\) \([A-Z]\)</b>|^<li[^>]*>(<span.*</span>)?\(\d{1,2}\) \((ix|iv|v?i{0,3})\) \([A-Z]\)|</li>$','', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_caps_alphabet)
                        caps_alpha = chr(ord(caps_alpha) + 1)
                        li_tag_for_number = self.soup.new_tag("li")
                        li_tag_for_number['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}"
                        li_tag_for_roman = self.soup.new_tag("li")
                        li_tag_for_roman['id'] = f"{h3_id}ol{ol_count}{ol_id_of_roman}"
                        li_tag_for_number['class'] = "number"
                        li_tag.append(ol_tag_for_roman)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}{ol_id_of_roman}{alphabet_id}"
                        li_tag_for_roman['class'] = "roman"
                        li_tag_for_roman.append(ol_tag_for_caps_alphabet)
                        ol_tag_for_roman.append(li_tag_for_roman)
                        li_tag_for_number.append(ol_tag_for_roman)
                        ol_tag_for_number.append(li_tag_for_number)
                        number += 1
                        roman_number = roman.fromRoman(ol_id_of_roman.upper())
                        roman_number += 1
                        roman_number = roman.toRoman(roman_number).lower()
                    elif re.search('^\([a-z]\) \(\d\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        ol_id_of_alphabet = re.search('^\((?P<ol_id_alphabet>[a-z])\)', tag.text.strip()).group('ol_id_alphabet')
                        ol_id_of_number = re.search('\((?P<ol_id_number>\d{1,2})\)', tag.text.strip()).group('ol_id_number')
                        tag_string = re.sub('^<li[^>]*>(<span.*</span>)?<b>\([a-z]\) \(\d\)</b>|^<li[^>]*>(<span.*</span>)?\([a-z]\) \(\d\)|</li>$','', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_number)
                        number += 1
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{h3_id}ol{ol_count}{ol_id_of_alphabet}"
                        li_tag['class'] = "alphabet"
                        ol_tag_for_number.wrap(li_tag)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{ol_id_of_alphabet}{ol_id_of_number}"
                        tag['class'] = "number"
                        li_tag.wrap(ol_tag_for_alphabet)
                        alphabet = chr(ord(alphabet) + 1)
                        if re.search('^[a-z A-Z]+', next_tag.text.strip()):
                            while re.search("^[a-z A-Z]+", next_tag.text.strip()):
                                sub_tag = next_tag.find_next_sibling()
                                p_tag = self.soup.new_tag("p")
                                p_tag.string = next_tag.text
                                p_tag['id'] = f"{tag['id']}.{count_of_p_tag}"
                                count_of_p_tag += 1
                                p_tag['class'] = next_tag['class']
                                tag.append(p_tag)
                                next_tag.decompose()
                                next_tag = sub_tag
                            count_of_p_tag = 1
                    elif re.search('^\(\d{1,2}\) \((ix|iv|v?i{0,3})\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        ol_id_of_number = re.search('^\((?P<ol_id_number>\d{1,2})\)', tag.text.strip()).group('ol_id_number')
                        ol_id_of_roman = re.search('\((?P<ol_id_roman>(ix|iv|v?i{0,3}))\)', tag.text.strip()).group('ol_id_roman')
                        tag_string = re.sub('^<li[^>]*>(<span.*</span>)?<b>\(\d{1,2}\) \((ix|iv|v?i{0,3})\)</b>|^<li[^>]*>(<span.*</span>)?\(\d{1,2}\) \((ix|iv|v?i{0,3})\)|</li>$','', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_roman)
                        roman_number = roman.fromRoman(ol_id_of_roman.upper())
                        roman_number += 1
                        roman_number = roman.toRoman(roman_number).lower()
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}"
                        li_tag['class'] = "number"
                        li_tag.append(ol_tag_for_roman)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}{ol_id_of_roman}"
                        tag['class'] = "roman"
                        ol_tag_for_number.append(li_tag)
                        number += 1
                    elif re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\) \([A-Z]\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        alphabet_id = re.search('\((?P<alphabet_id>[A-Z])\)', tag.text.strip()).group('alphabet_id')
                        roman_id = re.search('\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)',tag.text.strip()).group('roman_id')
                        tag_string = re.sub('^<li[^>]*>(<span.*</span>)?<b>\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\) \([A-Z]\)</b>|^<li[^>]*>(<span.*</span>)?\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\) \([A-Z]\)|</li>$','', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_caps_alphabet)
                        caps_alpha = chr(ord(caps_alpha) + 1)
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{h3_id}ol{ol_count}{roman_id}"
                        li_tag['class'] = "roman"
                        li_tag.append(ol_tag_for_caps_alphabet)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{roman_id}{alphabet_id}"
                        ol_tag_for_roman.append(li_tag)
                        roman_number = roman.fromRoman(roman_id.upper())
                        roman_number += 1
                        roman_number = roman.toRoman(roman_number).lower()
                    elif re.search('^\(\d{1,2}\) \([A-Z]\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        ol_id_of_number = re.search('^\((?P<ol_id_number>\d{1,2})\)', tag.text.strip()).group(
                            'ol_id_number')
                        ol_id_of_caps_alpha = re.search('\((?P<ol_id_of_caps_alpha>[A-Z])\)', tag.text.strip()).group(
                            'ol_id_of_caps_alpha')
                        tag_string = re.sub(
                            '^<li[^>]*>(<span.*</span>)?<b>\(\d{1,2}\) \([A-Z]\)</b>|^<li[^>]*>(<span.*</span>)?\(\d{1,2}\) \([A-Z]\)|</li>$',
                            '', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_caps_alphabet)
                        caps_alpha = chr(ord(caps_alpha) + 1)
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}"
                        li_tag['class'] = "number"
                        li_tag.append(ol_tag_for_caps_alphabet)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{ol_id_of_number}{ol_id_of_caps_alpha}"
                        ol_tag_for_number.append(li_tag)
                        number += 1
                    elif re.search(f'^\({caps_alpha}\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        caps_alphabet_id = re.search('^\((?P<caps_alphabet_id>[A-Z])\)', tag.text.strip()).group(
                            'caps_alphabet_id')
                        tag_string = re.sub(
                            '^<li[^>]*>(<span.*</span>)?<b>\([A-Z]\)</b>|^<li[^>]*>(<span.*</span>)?\([A-Z]\)|</li>$',
                            '', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_caps_alphabet)
                        caps_alpha = chr(ord(caps_alpha) + 1)
                        if ol_tag_for_roman.li:
                            id_of_last_li = ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{caps_alphabet_id}"
                        else:
                            id_of_last_li = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{caps_alphabet_id}"
                        if re.search('^[a-z A-Z]+', next_tag.text.strip()):
                            while re.search("^[a-z A-Z]+", next_tag.text.strip()):
                                sub_tag = next_tag.find_next_sibling()
                                p_tag = self.soup.new_tag("p")
                                p_tag.string = next_tag.text
                                p_tag['class'] = next_tag['class']
                                tag.append(p_tag)
                                id_of_last_li = ol_tag_for_caps_alphabet.find_all("li")[-1].attrs['id']
                                p_tag['id'] = f"{id_of_last_li}.{count_of_p_tag}"
                                count_of_p_tag += 1
                                p_tag['class'] = next_tag['class']
                                next_tag.decompose()
                                ol_tag_for_caps_alphabet.append(tag)
                                next_tag = sub_tag
                            count_of_p_tag = 1
                        if re.search(f'^\({roman_number}\)', next_tag.text.strip()):
                            if ol_tag_for_roman.li:
                                ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                caps_alpha = 'A'
                        elif re.search(f'^\({number}\)', next_tag.text.strip()):
                            if ol_tag_for_roman.li:
                                ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                caps_alpha = 'A'
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = 'i'
                            else:
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_caps_alphabet)
                                ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                caps_alpha = 'A'
                        elif re.search(f'^\({alphabet}\)', next_tag.text.strip()):
                            ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                            ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                            ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                            caps_alpha = 'A'
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            roman_number = 'i'
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                    elif re.search(f'^\({caps_roman}\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        roman_id = re.search('^\((?P<roman_id>(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))\)',tag.text.strip()).group('roman_id')
                        tag_string = re.sub('^<li[^>]*>(<span.*</span>)?<b>\((XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\)</b>|^<li[^>]*>(<span.*</span>)?\((XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\)|</li>$','', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_caps_roman)
                        caps_roman = roman.fromRoman(roman_id)
                        caps_roman += 1
                        caps_roman = roman.toRoman(caps_roman)
                        id_of_last_li = ol_tag_for_caps_alphabet.find_all("li")[-1].attrs['id']
                        tag['id'] = f"{id_of_last_li}{roman_id}"
                        if re.search(f'^\({caps_alpha}\)', next_tag.text.strip()):
                            ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_caps_roman)
                            ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                            caps_roman = 'I'
                        elif re.search(f'^\({roman}\)', next_tag.text.strip()):
                            ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_caps_roman)
                            ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                            ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                            caps_roman = 'I'
                            ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                            caps_alpha = 'A'
                        elif re.search(f'^\({number}\)',next_tag.text.strip()):
                            ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_caps_roman)
                            ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                            ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                            ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                            caps_roman = 'I'
                            ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                            caps_alpha = 'A'
                            ol_tag_for_roman=self.soup.new_tag("ol",type="i")
                            roman_number ="i"
                    elif re.search(f'^\({alphabet}{alphabet}?\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        alphabet_id = re.search(f'^\((?P<alphabet_id>{alphabet}{alphabet}?)\)',tag.text.strip()).group('alphabet_id')
                        text = str(tag)
                        tag_string = re.sub('^<li[^>]*>(<span.*</span>)?<b>\([a-z]+\)</b>|^<li[^>]*>(<span.*</span>)?\([a-z]+\)|</li>$','', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        if ol_tag_for_number.li:
                            tag.wrap(ol_tag_for_inner_alphabet)
                            inner_alphabet = chr(ord(inner_alphabet) + 1)
                            number_id = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id']
                            tag.attrs['id'] = f"{number_id}{alphabet_id}"
                            if re.search(f'^\({number}\)', next_tag.text.strip()):
                                if ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_inner_alphabet)
                                    ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                    inner_alphabet = 'a'
                        else:
                            tag.wrap(ol_tag_for_alphabet)
                            if alphabet == "z":
                                alphabet = 'a'
                            else:
                                alphabet = chr(ord(alphabet) + 1)
                            tag.attrs['id'] = f"{h3_id}ol{ol_count}{alphabet_id}"
                            tag['class'] = "alphabet"
                            if re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})', next_tag.text.strip(),
                                         re.IGNORECASE):  # Article 1
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                                ol_count = 1
                                continue
                            elif re.search('Section \d+', next_tag.text.strip()):
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                                if re.search('\(a\)|\(\d\)', next_tag.find_next_sibling().text.strip()):
                                    ol_count += 1
                            elif re.search('^“?[a-z A-Z]+', next_tag.text.strip()):
                                while re.search("^“?[a-z A-Z]+", next_tag.text.strip()) and next_tag.name != "h4":
                                    sub_tag = next_tag.find_next_sibling()
                                    p_tag = self.soup.new_tag("p")
                                    count_of_p_tag += 1
                                    p_tag.string = next_tag.text
                                    tag.append(p_tag)
                                    id_of_last_li = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs[
                                        'id']
                                    p_tag['id'] = f"{id_of_last_li}.{count_of_p_tag}"
                                    p_tag['class'] = next_tag['class']
                                    ol_tag_for_alphabet.append(tag)
                                    next_tag.decompose()
                                    next_tag = sub_tag
                                if next_tag.name == "h4":
                                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                    alphabet = 'a'
                            elif next_tag.name == "h4":
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                    elif re.search(f'^\({inner_alphabet}\)',tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        alphabet_id = re.search('^\((?P<alphabet_id>[a-z]+)\)', tag.text.strip()).group('alphabet_id')
                        text = str(tag)
                        tag_string = re.sub('^<li[^>]*>(<span.*</span>)?<b>\([a-z]+\)</b>|^<li[^>]*>(<span.*</span>)?\([a-z]+\)|</li>$','', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_inner_alphabet)
                        inner_alphabet = chr(ord(inner_alphabet) + 1)
                        number_id = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id']
                        tag.attrs['id'] = f"{number_id}{alphabet_id}"
                        if re.search(f'^\({number}\)', next_tag.text.strip()):
                            if ol_tag_for_number.li:
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_inner_alphabet)
                                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                                inner_alphabet = 'a'

                    elif re.search(f'^\({roman_number}\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        roman_id = re.search('^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)',tag.text.strip()).group('roman_id')
                        tag_string = re.sub('^<li[^>]*>(<span.*</span>)?<b>\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)</b>|^<li[^>]*>(<span.*</span>)?\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)|</li>$','', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_roman)
                        roman_number = roman.fromRoman(roman_id.upper())
                        roman_number += 1
                        roman_number = roman.toRoman(roman_number).lower()
                        tag['class'] = "roman"
                        if ol_tag_for_number.li:
                            id_of_last_li = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{roman_id}"
                        elif ol_tag_for_alphabet.li:
                            id_of_last_li = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{roman_id}"
                        if re.search('^“?[a-z A-Z]+',next_tag.text.strip()) or next_tag.next_element.name == "br":  # 5-31.1-1. after 16i 2 break
                            while re.search("^“?[a-z A-Z]+", next_tag.text.strip()) and next_tag.name!="h4":
                                sub_tag = next_tag.find_next_sibling()
                                p_tag = self.soup.new_tag("p")
                                p_tag.string = next_tag.text
                                tag.append(p_tag)
                                id_of_last_li = ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs['id']
                                p_tag['class'] = next_tag['class']
                                p_tag['id'] = f"{id_of_last_li}.{count_of_p_tag}"
                                count_of_p_tag += 1
                                ol_tag_for_roman.append(tag)
                                next_tag.decompose()
                                next_tag = sub_tag
                            count_of_p_tag = 1
                            if next_tag.name=="h4":
                                if ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li",class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_roman=self.soup.new_tag("ol",type="i")
                                    ol_tag_for_number=self.soup.new_tag("ol")
                                    roman_number="i"
                                    number=1
                            while next_tag.next_element.name == "br":
                                sub_tag = next_tag.find_next_sibling()
                                next_tag.decompose()
                                next_tag = sub_tag
                        if re.search('^\(\d{1,2}\)', next_tag.text.strip()):
                            if ol_tag_for_caps_alphabet.li:
                                ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_roman)
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                    ol_tag_for_caps_alphabet)
                                ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                caps_alpha = 'A'
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = 'i'
                            elif ol_tag_for_number.li:
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                roman_number = 'i'
                        elif re.search('^\([a-z]+\)', next_tag.text.strip()):
                            alphabet_id = re.search('^\((?P<alphabet_id>[a-z]+)\)', next_tag.text.strip()).group(
                                'alphabet_id')
                            if alphabet == alphabet_id:
                                if ol_tag_for_number.li:  # a 1 i
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                        ol_tag_for_number)
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = 'i'
                                    ol_tag_for_number = self.soup.new_tag("ol")
                                    number = 1
                                elif ol_tag_for_alphabet.li:  # a i
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                        ol_tag_for_roman)
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = 'i'
                            else:
                                continue
                    elif re.search(f'^\({inner_roman}\)', tag.text):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        roman_id = re.search('^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)',tag.text.strip()).group('roman_id')
                        tag_string = re.sub('^<li[^>]*>(<span.*</span>)?<b>\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)</b>|^<li[^>]*>(<span.*</span>)?\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)|</li>$','', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_inner_roman)
                        inner_roman = roman.fromRoman(roman_id.upper())
                        inner_roman += 1
                        inner_roman = roman.toRoman(inner_roman).lower()
                        if ol_tag_for_inner_number.li:
                            id_of_last_li = ol_tag_for_inner_number.find_all("li")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{roman_id}"
                        elif ol_tag_for_caps_alphabet.li:
                            id_of_last_li = ol_tag_for_caps_alphabet.find_all("li")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{roman_id}"
                        if re.search(f'^\({number}\)', next_tag.text.strip()):
                            if ol_tag_for_inner_number.li:
                                ol_tag_for_inner_number.find_all("li")[-1].append(ol_tag_for_inner_roman)
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                inner_roman = 'i'
                            elif ol_tag_for_caps_alphabet.li:
                                ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_inner_roman)
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                roman_number = 'i'
                        elif re.search(f'^\({caps_alpha}\)', next_tag.text.strip()):
                            if ol_tag_for_inner_number.li:
                                ol_tag_for_inner_number.find_all("li")[-1].append(ol_tag_for_inner_roman)
                                ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_inner_number)
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                ol_tag_for_inner_number = self.soup.new_tag("ol")
                                inner_roman = 'i'
                                inner_num = 1
                            elif ol_tag_for_caps_alphabet.li:
                                ol_tag_for_caps_alphabet.find_all("li")[-1].append(ol_tag_for_inner_roman)
                                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                inner_roman = 'i'
                        else:
                            continue
                    elif re.search(f'^\({number}\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        number_id = re.search('^\((?P<ol_id>\d{1,2})\)', tag.text.strip()).group('ol_id')
                        tag_string = re.sub('^<li[^>]*>(<span.*</span>)?<b>\(\d{1,2}\)</b>|^<li[^>]*>(<span.*</span>)?\(\d{1,2}\)|</li>$','', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag['class'] = "number"
                        if ol_tag_for_alphabet.li:
                            id_of_last_li = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs['id']  # (a) (1)
                            tag['id'] = f"{id_of_last_li}{number_id}"
                        else:
                            tag['id'] = f"{h3_id}ol{ol_count}{number_id}"
                        if ol_tag_for_number.li:  # 4-13-1
                            ol_tag_for_number.append(tag)
                        else:
                            tag.wrap(ol_tag_for_number)
                        number += 1

                        if re.search('Section \d+', next_tag.text.strip()):
                            if ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                            if re.search('^\(a\)|^\(\d\)', next_tag.find_next_sibling().text.strip()):
                                ol_count += 1
                        elif re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})', next_tag.text.strip()):
                            if ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                            ol_count = 1
                        elif re.search('^[a-z A-Z]+', next_tag.text.strip()) or next_tag.next_element.name == "br":
                            if next_tag.find_next_sibling().name == "h4":
                                if ol_tag_for_alphabet.li:
                                    ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_number = self.soup.new_tag("ol")
                                number = 1
                            else:
                                while next_tag.name != "h4" and (re.search("^[a-z A-Z]+",next_tag.text.strip()) or next_tag.next_element.name == "br"):  # 123 text history of section
                                    if next_tag.next_element.name == "br":
                                        sub_tag = next_tag.find_next_sibling()
                                        next_tag.decompose()
                                        next_tag = sub_tag
                                    else:
                                        sub_tag = next_tag.find_next_sibling()
                                        p_tag = self.soup.new_tag("p")
                                        p_tag.string = next_tag.text
                                        p_tag['class'] = next_tag['class']
                                        tag.append(p_tag)
                                        id_of_last_li = ol_tag_for_number.find_all("li", class_="number")[-1].attrs[
                                            'id']
                                        p_tag['id'] = f"{id_of_last_li}.{count_of_p_tag}"
                                        count_of_p_tag += 1
                                        ol_tag_for_number.append(tag)
                                        next_tag.decompose()
                                        next_tag = sub_tag
                                count_of_p_tag = 1
                                if re.search(f"^\({alphabet}\)", next_tag.text.strip()):
                                    if ol_tag_for_alphabet.li:
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                        ol_tag_for_number = self.soup.new_tag("ol")
                                        number = 1
                                elif next_tag.name == "h4":
                                    if ol_tag_for_alphabet.li:
                                        ol_tag_for_alphabet.append(ol_tag_for_number)
                                        ol_tag_for_number = self.soup.new_tag("ol")
                                        number = 1
                                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                        alphabet = 'a'
                                    else:
                                        ol_tag_for_number = self.soup.new_tag("ol")
                                        number = 1

                        elif re.search(f'^\({alphabet}\)', next_tag.text.strip()):
                            if ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_number = self.soup.new_tag("ol")
                                number = 1
                    elif re.search(f'^\({inner_num}\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        number_id = re.search('^\((?P<ol_id>\d{1,2})\)', tag.text.strip()).group('ol_id')
                        tag_string = re.sub('^<li[^>]*>(<span.*</span>)?<b>\(\d{1,2}\)</b>|^<li[^>]*>(<span.*</span>)?\(\d{1,2}\)|</li>$','', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        if ol_tag_for_caps_alphabet.li:
                            id_of_last_li = ol_tag_for_caps_alphabet.find_all("li")[-1].attrs['id']
                            # (a) (1)
                        elif ol_tag_for_number.li:
                            id_of_last_li = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id']
                        tag['id'] = f"{id_of_last_li}{number_id}"
                        ol_tag_for_inner_number.append(tag)
                        inner_num += 1
                        if re.search('^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', next_tag.text.strip()):  # roman i
                            roman_id = re.search('^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)',
                                                 next_tag.text.strip()).group('roman_id')
                            if roman_number == roman_id and ol_tag_for_number.li:
                                ol_tag_for_caps_alphabet.append(ol_tag_for_inner_number)
                                ol_tag_for_roman.append(ol_tag_for_caps_alphabet)
                else:
                    if re.search(f'^\({alphabet}{alphabet}?\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        alphabet_id = re.search(f'^\((?P<alphabet_id>{alphabet}{alphabet}?)\)', tag.text.strip()).group('alphabet_id')
                        tag_string = re.sub(
                            '^<li[^>]*>(<span.*</span>)?<b>\([a-z]+\)</b>|^<li[^>]*>(<span.*</span>)?\([a-z]+\)|</li>$',
                            '', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_alphabet)
                        tag.attrs['id'] = f"{h3_id}ol{ol_count}{alphabet_id}"
                        tag['class'] = "alphabet"
                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                        alphabet = 'a'
                    elif re.search(f'^\({roman_number}\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        roman_id = re.search('^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)',
                                             tag.text.strip()).group('roman_id')
                        tag_string = re.sub(
                            '^<li[^>]*>(<span.*</span>)?<b>\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)</b>|^<li[^>]*>(<span.*</span>)?\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)|</li>$',
                            '', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_roman)
                        tag['id'] = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id'] + roman_id
                        tag['class'] = "roman"
                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                        if ol_tag_for_alphabet.li:
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                            ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                            alphabet = 'a'
                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                        roman_number = 'i'
                        ol_tag_for_number = self.soup.new_tag("ol")
                        number = 1
                    elif re.search(f'^\({number}\)', tag.text.strip()):
                        tag.name = "li"
                        h3_id = tag.find_previous_sibling("h3").attrs['id']
                        text = str(tag)
                        number_id = re.search('^\((?P<ol_id>\d{1,2})\)', tag.text.strip()).group('ol_id')
                        tag_string = re.sub(
                            '^<li[^>]*>(<span.*</span>)?<b>\(\d{1,2}\)</b>|^<li[^>]*>(<span.*</span>)?\(\d{1,2}\)|</li>$',
                            '', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag['class'] = "number"
                        tag.wrap(ol_tag_for_number)
                        if ol_tag_for_alphabet.li:
                            id_of_last_li = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{number_id}"
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                        else:
                            tag['id'] = f"{h3_id}ol{ol_count}{number_id}"
                        ol_tag_for_number = self.soup.new_tag("ol")
                        number = 1
                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                        alphabet = 'a'
                    elif re.search(f'^\({caps_alpha}\)', tag.text.strip()):
                        tag.name = "li"
                        text = str(tag)
                        caps_alphabet_id = re.search('^\((?P<caps_alphabet_id>[A-Z])\)', tag.text.strip()).group(
                            'caps_alphabet_id')
                        tag_string = re.sub(
                            '^<li[^>]*>(<span.*</span>)?<b>\([A-Z]\)</b>|^<li[^>]*>(<span.*</span>)?\([A-Z]\)|</li>$',
                            '', text.strip())
                        tag.clear()
                        tag.append(BeautifulSoup(tag_string, features="html.parser"))
                        tag.wrap(ol_tag_for_caps_alphabet)
                        if ol_tag_for_roman.li:
                            id_of_last_li = ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{caps_alphabet_id}"
                            ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_caps_alphabet)
                            ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                            if ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                            ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                            caps_alpha = 'A'
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            roman_number = "i"
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                            ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                            alphabet = 'a'
                        else:
                            id_of_last_li = ol_tag_for_number.find_all("li", class_="number")[-1].attrs['id']
                            tag['id'] = f"{id_of_last_li}{caps_alphabet_id}"
                            ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_caps_alphabet)
                            if ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                alphabet = 'a'
                            ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                            caps_alpha = 'A'
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1

    def create_div_tag(self):
        div_tag_for_chapter = self.soup.new_tag("div")
        div_tag_for_section = self.soup.new_tag("div")
        div_tag_for_h4 = self.soup.new_tag("div")
        div_tag_for_h5 = self.soup.new_tag("div")
        div_tag_for_article = self.soup.new_tag("div")
        for tag in self.soup.find_all("h2"):
            next_tag = tag.find_next_sibling()
            tag.wrap(div_tag_for_chapter)
            if next_tag.name == "nav":
                sibling_of_nav = next_tag.find_next_sibling()
                div_tag_for_chapter.append(next_tag)
                next_tag = sibling_of_nav
                if next_tag.name == "h4":
                    sibling_of_h4 = next_tag.find_next_sibling()
                    div_tag_for_h4.append(next_tag)
                    next_tag = sibling_of_h4
                    while next_tag.name == "p":
                        sibling_of_p = next_tag.find_next_sibling()
                        div_tag_for_h4.append(next_tag)
                        next_tag = sibling_of_p
                    div_tag_for_chapter.append(div_tag_for_h4)
                    div_tag_for_h4 = self.soup.new_tag("div")
                if next_tag.name == "h3":
                    tag_of_h3 = next_tag.find_next_sibling()
                    if re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})', next_tag.text.strip()):
                        next_tag.wrap(div_tag_for_article)
                    else:
                        next_tag.wrap(div_tag_for_section)
                    while tag_of_h3 and tag_of_h3.name != "h2":
                        if tag_of_h3.name == "h4":
                            tag_of_h4 = tag_of_h3.find_next_sibling()
                            tag_of_h3.wrap(div_tag_for_h4)
                            while tag_of_h4 and tag_of_h4.name != "h4" and tag_of_h4.name != "h2":
                                if tag_of_h4.name == "h3":
                                    if div_tag_for_h4.next_element:
                                        div_tag_for_section.append(div_tag_for_h4)
                                        div_tag_for_h4 = self.soup.new_tag("div")
                                    if re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})', tag_of_h4.text.strip()):
                                        next_tag = tag_of_h4.find_next_sibling()
                                        tag_of_h4.wrap(div_tag_for_article)
                                        tag_of_h4 = next_tag
                                        while tag_of_h4.name == "p" or tag_of_h4.name == "h3":
                                            if tag_of_h4.name == "h3" and re.search(
                                                    '^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})',
                                                    tag_of_h4.text.strip()):
                                                next_tag = tag_of_h4.find_next_sibling()
                                                div_tag_for_section.append(div_tag_for_article)
                                                div_tag_for_article = self.soup.new_tag("div")
                                                div_tag_for_article.append(tag_of_h4)
                                                tag_of_h4 = next_tag
                                            elif tag_of_h4['class'][0] == self.dictionary_to_store_class_name[
                                                'History']:
                                                next_tag = tag_of_h4.find_next_sibling()
                                                div_tag_for_article.append(tag_of_h4)
                                                tag_of_h4 = next_tag
                                            elif tag_of_h4['class'][0] == self.dictionary_to_store_class_name['h4']:
                                                div_tag_for_section.append(div_tag_for_article)
                                                div_tag_for_article = self.soup.new_tag("div")
                                                break
                                        div_tag_for_section.append(div_tag_for_article)
                                        div_tag_for_article = self.soup.new_tag("div")
                                    else:  # 2-13-1
                                        if div_tag_for_section.next_element:
                                            div_tag_for_chapter.append(div_tag_for_section)
                                        div_tag_for_section = self.soup.new_tag("div")
                                        next_tag = tag_of_h4.find_next_sibling()
                                        div_tag_for_section.append(tag_of_h4)
                                        tag_of_h4 = next_tag
                                        if tag_of_h4.name == "p":
                                            next_tag = tag_of_h4.find_next_sibling()
                                            div_tag_for_section.append(tag_of_h4)
                                            tag_of_h4 = next_tag

                                elif tag_of_h4.name == "h5":
                                    tag_of_h5 = tag_of_h4.find_next_sibling()
                                    tag_of_h4.wrap(div_tag_for_h5)
                                    while tag_of_h5.name != "h5" and tag_of_h5.name != "h3":
                                        if tag_of_h5.next_element.name == "br":
                                            next_tag = tag_of_h5.find_next_sibling()
                                            div_tag_for_h4.append(div_tag_for_h5)
                                            div_tag_for_h5 = self.soup.new_tag("div")
                                            div_tag_for_section.append(div_tag_for_h4)
                                            div_tag_for_h4 = self.soup.new_tag("div")
                                            div_tag_for_section.append(tag_of_h5)
                                            tag_of_h5 = next_tag
                                        elif tag_of_h5.name == "h4":
                                            div_tag_for_h4.append(div_tag_for_h5)
                                            div_tag_for_h5 = self.soup.new_tag("div")
                                            div_tag_for_section.append(div_tag_for_h4)
                                            div_tag_for_h4 = self.soup.new_tag("div")
                                            break
                                        elif tag_of_h5.name == "h2":
                                            div_tag_for_chapter.append(div_tag_for_section)
                                            div_tag_for_section = self.soup.new_tag("div")
                                            div_tag_for_chapter = self.soup.new_tag("div")
                                            break
                                        else:
                                            next_tag = tag_of_h5.find_next_sibling()
                                            div_tag_for_h5.append(tag_of_h5)
                                            tag_of_h5 = next_tag
                                    if div_tag_for_h5.next_element:
                                        div_tag_for_h4.append(div_tag_for_h5)
                                    div_tag_for_h5 = self.soup.new_tag("div")
                                    tag_of_h4 = tag_of_h5
                                elif tag_of_h4.next_element.name == "br":
                                    next_tag = tag_of_h4.find_next_sibling()
                                    div_tag_for_section.append(div_tag_for_h4)
                                    div_tag_for_h4 = self.soup.new_tag("div")
                                    div_tag_for_section.append(tag_of_h4)
                                    tag_of_h4 = next_tag
                                    if tag_of_h4.name == "h2":
                                        div_tag_for_chapter.append(div_tag_for_section)
                                        div_tag_for_section = self.soup.new_tag("div")
                                        div_tag_for_chapter = self.soup.new_tag("div")
                                elif tag_of_h4.name == "nav":
                                    next_tag = tag_of_h4.find_next_sibling()
                                    div_tag_for_h4.append(tag_of_h4)
                                    tag_of_h4 = next_tag
                                elif tag_of_h4.name == "ol":
                                    next_tag = tag_of_h4.find_next_sibling()
                                    div_tag_for_section.append(tag_of_h4)
                                    tag_of_h4 = next_tag
                                elif tag_of_h4.name == "p":
                                    next_tag = tag_of_h4.find_next_sibling()
                                    if tag_of_h4.text.isupper():  # after article caps title
                                        if div_tag_for_h4.next_element:
                                            div_tag_for_section.append(div_tag_for_h4)
                                            div_tag_for_h4 = self.soup.new_tag("div")
                                        div_tag_for_section.append(tag_of_h4)
                                    else:
                                        if div_tag_for_h4.next_element:
                                            div_tag_for_h4.append(tag_of_h4)
                                        else:
                                            div_tag_for_section.append(tag_of_h4)
                                    tag_of_h4 = next_tag

                            if div_tag_for_h4.next_element:
                                div_tag_for_section.append(div_tag_for_h4)
                                div_tag_for_h4 = self.soup.new_tag("div")
                        elif tag_of_h3.name == "h3" and re.search('^ARTICLE (XC|XL|L?X{0,3})(IX|IV|V?I{0,3})',
                                                                  tag_of_h3.text.strip()):
                            next_tag = tag_of_h3.find_next_sibling()
                            div_tag_for_article.append(tag_of_h3)
                            tag_of_h3 = next_tag
                            # chapter 24
                            while tag_of_h3.name != "h3" and tag_of_h3.name != "h4":
                                next_tag = tag_of_h3.find_next_sibling()
                                div_tag_for_article.append(tag_of_h3)
                                tag_of_h3 = next_tag
                            div_tag_for_section.append(div_tag_for_article)
                            div_tag_for_article = self.soup.new_tag("div")
                        else:
                            next_tag = tag_of_h3.find_next_sibling()
                            div_tag_for_section.append(tag_of_h3)
                        tag_of_h3 = next_tag

                    if div_tag_for_section.next_element:
                        div_tag_for_chapter.append(div_tag_for_section)
                        div_tag_for_section = self.soup.new_tag("div")
                        div_tag_for_chapter = self.soup.new_tag("div")

    def remove_class_name(self):
        for tag in self.soup.find_all():
            if tag.name not in ["ul", "li","h2","p"] :
                del tag['class']
            if tag.name in["ul","li","h2","p"]:
                if tag['class'] not in  ["chapter","leaders","transformation"]:
                    del tag['class']

    def remove_from_head(self):
        list_to_remove_from_head=['text/css','LEXIS Publishing']
        for tag in self.soup.find_all('meta'):
            if tag['content'] in list_to_remove_from_head :
                tag.decompose()
        meta_tag=self.soup.find('meta',attrs={'name':'Description'})
        meta_tag.decompose()
        style_tag=self.soup.find('style')
        style_tag.decompose()

    def adding_css_to_file(self):
        head_tag = self.soup.find("head")
        link_tag = self.soup.new_tag("link", rel="stylesheet",href="https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css")
        head_tag.append(link_tag)

    def add_watermark(self):
        meta_tag = self.soup.new_tag('meta')
        meta_tag_for_water_mark=self.soup.new_tag('meta')
        meta_tag['content']="width=device-width, initial-scale=1"
        meta_tag['name']="viewport"
        meta_tag_for_water_mark.attrs['name'] = "description"
        meta_tag_for_water_mark.attrs['content'] = "Release 70 of the Official Code of Rhode Island Annotated released 2021.11.Transformed and posted by Public.Resource.Org using rtf-parser.py version 1.0 on 2022-06-13.This document is not subject to copyright and is in the public domain."
        self.soup.head.append(meta_tag)
        self.soup.head.append(meta_tag_for_water_mark)

    def write_to_file(self):
        file_write = open("/home/mis/PycharmProjects/rhodeisland/venv/ricode/modified/gov.ri.code.title.46.html", "w")
        file_write.write(self.soup.prettify())


html_file = "/home/mis/PycharmProjects/rhodeisland/venv/ricode/raw/gov.ri.code.title.46.html"
unstructured_to_structured_html = UnstructuredHtmlToStructuredHtml()
unstructured_to_structured_html.create_soup(html_file)
unstructured_to_structured_html.get_class_name()
unstructured_to_structured_html.remove_junk()
unstructured_to_structured_html.convert_to_header_and_assign_id()
unstructured_to_structured_html.create_nav_and_ul_tag()
unstructured_to_structured_html.add_citation()
unstructured_to_structured_html.create_nav_and_main_tag()
unstructured_to_structured_html.create_ol_tag()
unstructured_to_structured_html.create_div_tag()
unstructured_to_structured_html.remove_class_name()
unstructured_to_structured_html.remove_from_head()
unstructured_to_structured_html.adding_css_to_file()
unstructured_to_structured_html.add_watermark()
unstructured_to_structured_html.write_to_file()
