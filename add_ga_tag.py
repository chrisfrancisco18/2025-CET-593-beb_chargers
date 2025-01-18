from bs4 import BeautifulSoup
import shutil
import pathlib
import logging
import streamlit as st


# Adapted from https://stackoverflow.com/questions/76034389/google-analytics-is-not-working-on-streamlit-application

analytics_js = """
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-FQB020CEQY"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'G-FQB020CEQY');
    </script>
    <div id="G-FQB020CEQY"></div>
    """
analytics_id = "G-FQB020CEQY"

# Identify html path of streamlit
index_path = pathlib.Path(st.__file__).parent / "static" / "index.html"
logging.info(f'editing {index_path}')
soup = BeautifulSoup(index_path.read_text(), features="html.parser")
if not soup.find(id=analytics_id):  # if id not found within html file
    bck_index = index_path.with_suffix('.bck')
    if bck_index.exists():
        shutil.copy(bck_index, index_path)  # backup recovery
    else:
        shutil.copy(index_path, bck_index)  # save backup
    html = str(soup)
    new_html = html.replace('<head>', '<head>\n' + analytics_js)
    index_path.write_text(new_html)  # insert analytics tag at top of head
