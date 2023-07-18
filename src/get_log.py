import logging


logging.basicConfig(filename="test.log",
                    filemode="w",
                    encoding='utf-8',
                    format="%(asctime)s %(levelname)s: %(message)s",
                    datefmt="%Y-%M-%d %H:%M:%S",
                    level=logging.DEBUG)

for i in range(100):
    logging.debug('This is a debug message' + str(i))
    logging.info('This is an info message' + str(i))
    logging.warning('This is a warning message' + str(i))
    logging.error('This is an error message' + str(i))
    logging.critical('This is a critical message' + str(i))

    try:
        a = 1/0
    except Exception as e:
        logging.error("Exception occurred" + str(i), exc_info=True)

    logging.debug('This is a debug message' + str(i))
    logging.info('This is an info message' + str(i))

    try:
        a = pow(1, 2, 3, 4)
    except Exception as e:
        logging.error("Exception occurred" + str(i), exc_info=True)

    logging.debug('This is a debug message' + str(i))
    logging.info('This is an info message' + str(i))
