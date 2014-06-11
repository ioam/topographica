/* Override sanitize Google Caja call in IPython 2.0 */
IPython.security.sanitize_html = function (html) { return html; };