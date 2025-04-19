import re

def markdown(text) -> str:
        """Escapes MardownV2 special Characters"""

        if type(text) is not str:
                return text
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)
 