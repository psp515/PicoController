from logging.logger import Logger


class HtmlBuilder:
    def __init__(self):
        self.logger = Logger()
        self.title = "Led Controller"
        self.styles = []
        self.body_content = []
        self.scripts = []

    def set_title(self, title):
        self.title = title

    def add_styles(self, path):
        try:
            with open(path, 'r') as file:
                style_content = file.read()
                self.styles.append(f'<style>{style_content}</style>')
        except Exception as e:
            self.logger.error(f"Error reading style file: {e}")

    def add_body(self, content):
        self.body_content.append(content)

    def add_scripts(self, script):
        self.scripts.append(script)

    def build(self):
        styles_html = "".join(self.styles)
        scripts_html = "".join(self.scripts)
        body_html = "".join(self.body_content)
        html = f"""<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.title}</title>
            {styles_html}
        </head>
        <body>
            {body_html}
            <script>
                {scripts_html}
            </script>
        </body>
        </html>
        """
        return html
