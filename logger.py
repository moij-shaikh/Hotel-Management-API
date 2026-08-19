import logging
formatter=logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s"
)

admin_logger=logging.getLogger("admin")

admin_handler=logging.FileHandler("Logs/admin.log")
admin_handler.setFormatter(formatter)
admin_logger.addHandler(admin_handler)
admin_logger.setLevel(logging.DEBUG)

user_logger=logging.getLogger("user")

user_handler=logging.FileHandler("Logs/user.log")
user_handler.setFormatter(formatter)
user_logger.addHandler(user_handler)
user_logger.setLevel(logging.DEBUG)