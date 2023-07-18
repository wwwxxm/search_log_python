import re
import os
import time
import json
import queue
import threading
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

results_folder = './results'

global global_log_queue, global_context_queue, global_fileCount, global_result_queue


class ResultEventHandler(FileSystemEventHandler):
    def __init__(self, observer):
        self.observer = observer
        self.last_change_time = time.time()

    def on_created(self, event):
        global global_result_queue
        print('event', event)

        if event.is_directory:
            return
        result_file_path = event.src_path
        with open(result_file_path, 'r') as f:
            result_data = f.read()
        global_result_queue.put(json.loads(result_data))


def start_oberve():
    observer = Observer()
    event_handler = ResultEventHandler(observer)
    observer.schedule(event_handler, results_folder, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(5)
            current_time = time.time()
            if current_time - event_handler.last_change_time > 10:
                observer.stop()
                break

    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def get_results():
    global global_result_queue
    try:
        print('global_result_queue size', global_result_queue.qsize())
        temp = global_result_queue.get(timeout=5)
        return temp
    except queue.Empty:
        return 'None'


def get_parser():
    # 使用命令行参数pattern（正则表达式匹配字符串）和context（查找日志上下行）
    parser = argparse.ArgumentParser()
    # python search_log.py -c 5
    parser.add_argument('-p', '--pattern', type=str,
                        default=r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}', help='pattern to search')
    # python search_log.py -p "(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}"
    parser.add_argument('-c', '--context', type=int,
                        default=2, help='context to search')
    args, unknown = parser.parse_known_args()
    return args


def write_results(maxSize: int = 10):
    #
    global global_log_queue, global_fileCount

    count = 0
    data = []
    while True:
        count += 1
        global_fileCount += 1

        # 从队列中获取数据
        try:
            temp = global_log_queue.get(timeout=5)
            data.append(temp)

            if count > maxSize:
                s = json.dumps(data, indent=4)

                with open('./results/' + str(global_fileCount) + 'results.json', 'w') as f:
                    f.write(s)
                data = []
                count = 0
        except queue.Empty:
            # 在指定时间内没有获取到数据
            print('No data in queue!')
            s = json.dumps(data, indent=4)
            with open('./results/' + str(global_fileCount) + 'results.json', 'w') as f:
                f.write(s)
            data = []
            count = 0
            break


def search_log(keywords: list, logPath: str):
    global global_log_queue, global_context_queue

    args = get_parser()

    detail_log = {}
    pre_line = ''
    line_num = 0
    cur_line_num = 0
    log_count = 0
    with open(logPath, 'r', encoding='gb2312') as f:
        while True:
            line_num += 1
            line = f.readline()
            if not line:
                if pre_line:
                    # 判断该条日志是否包含关键字
                    if any(keyword in pre_line for keyword in keywords):
                        pre_line = pre_line.strip()
                        if global_context_queue.full():
                            global_context_queue.get()
                        global_context_queue.put(
                            {'line': cur_line_num, 'message': pre_line})
                        details = [global_context_queue.get()
                                   for i in range(global_context_queue.qsize())]
                        temp = {
                            'line': cur_line_num,
                            'time': pre_line[:23],
                            'message': pre_line,
                            'detail': details
                        }
                        global_log_queue.put(temp)
                    else:
                        if detail_log.items():
                            if global_context_queue.full():
                                global_context_queue.get()
                            global_context_queue.put(
                                {'line': cur_line_num, 'message': pre_line})
                            index = list(detail_log.keys())[-1]
                            details = [global_context_queue.get()
                                       for i in range(global_context_queue.qsize())]
                            detail_log[index]['detail'] = details
                            global_log_queue.put(detail_log[index])
                            detail_log.pop(index)
                break

            # 获取一条日志
            pattern = re.compile(args.pattern)
            match = pattern.match(line)
            if match:
                log_count += 1
                if global_context_queue.full():
                    global_context_queue.get()
                global_context_queue.put(
                    {'line': cur_line_num, 'message': pre_line})
                # 队列已有日志的上下行
                index = log_count - args.context - 1
                if detail_log.get(index, None):
                    details = [global_context_queue.get()
                               for i in range(2*args.context+1)]
                    for i in details:
                        global_context_queue.put(i)
                    detail_log[index]['detail'] = details
                    global_log_queue.put(detail_log[index])
                    detail_log.pop(index)

                # 判断该条日志是否包含关键字
                if any(keyword in pre_line for keyword in keywords):
                    # 将该条日志写入文件
                    pre_line = pre_line.strip()
                    detail_log[log_count - 1] = {
                        'line': cur_line_num,
                        'time': pre_line[:23],
                        'message': pre_line,
                    }
                cur_line_num = line_num
                pre_line = line
            else:
                # 将该条日志与上一条日志合并
                pre_line = pre_line + line


def run_search(keywords=['ERROR'], logPath='./logs/test.log'):
    if not os.path.exists("results"):
        os.mkdir("results")
    for root, _, files in os.walk("results"):
        for file in files:
            file_path = os.path.join(root,file)
            os.remove(file_path)

    global global_log_queue, global_context_queue, global_fileCount, global_result_queue

    args = get_parser()

    # 创建全局队列对象
    global_log_queue = queue.Queue(1000)
    global_context_queue = queue.Queue(2*args.context+1)
    global_fileCount = 0
    global_result_queue = queue.Queue(10000)

    # 创建线程对象
    t1 = threading.Thread(target=write_results, args=(20,))
    t2 = threading.Thread(target=search_log, args=(keywords, logPath))
    t3 = threading.Thread(target=start_oberve)
    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()
    print('Finished!')


if __name__ == '__main__':
    run_search()
