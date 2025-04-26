import logging

class ColorFormatter(logging.Formatter):
    COLOR_CODES = {
        'DEBUG': "\033[94m",    # 蓝色
        'INFO': "\033[92m",     # 绿色
        'WARNING': "\033[93m",  # 黄色
        'ERROR': "\033[91m",    # 红色
        'CRITICAL': "\033[95m", # 紫红色
    }
    RESET_CODE = "\033[0m"

    def format(self, record):
        color_code = self.COLOR_CODES.get(record.levelname, self.RESET_CODE)
        message = super().format(record)
        return f"{color_code}{message}{self.RESET_CODE}"

# 创建Logger
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# Handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# 设置彩色Formatter
formatter = ColorFormatter('%(asctime)s %(levelname)s: %(message)s')
ch.setFormatter(formatter)

log.addHandler(ch)
