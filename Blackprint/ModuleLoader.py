import sys
import time, os
import importlib
import importlib.util

def reload_scripts(folder_path, ignore_list):
    for root, dirs, files in os.walk(folder_path):
        if(len(ignore_list) != 0):
            if any(ignored_folder in root for ignored_folder in ignore_list):
                continue

        for file in files:
            reload_script(file, os.path.join(root, file), folder_path)

def reload_script(file, file_path, folder_path):
    if file.endswith(".py") and not file.startswith("__"):
        rel_path = os.path.relpath(file_path, folder_path)
        module_name = os.path.splitext(rel_path)[0].replace(os.sep, ".")
        full_module_name = f"{__name__}.root.{module_name}"

        try:
            spec = importlib.util.spec_from_file_location(full_module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[full_module_name] = module
            spec.loader.exec_module(module)
        except Exception as e:
            import traceback
            print(f"Failed to reload {file_path}: {e}")
            traceback.print_exception(type(e), e, e.__traceback__)

watched_paths = {}
def AddModulePathHotReload(folder_path, onReload=None, ignore_list={}):
    global watched_paths
    if folder_path in watched_paths:
        return

    from threading import Thread
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    class ScriptReloader(FileSystemEventHandler):
        def __init__(self, folder_path):
            self.folder_path = folder_path
            self.last_reload_time = 0

        def on_modified(self, event):
            if event.src_path.endswith(".py"):
                now = time.time()
                
                if(len(ignore_list) != 0):
                    if any(ignored_folder in event.src_path for ignored_folder in ignore_list):
                        return

                # Debounce, avoid reloading too quickly
                if now - self.last_reload_time > 0.5:
                    print(f"Reloading: {event.src_path}")
                    reload_script(os.path.basename(event.src_path), event.src_path, self.folder_path)
                    self.last_reload_time = now
                    onReload(event.src_path) if onReload else None

    reloader = ScriptReloader(folder_path)
    reload_scripts(reloader.folder_path, ignore_list) # first run

    observer = Observer()
    observer.schedule(reloader, folder_path, recursive=True)
    observer_thread = Thread(target=observer.start)
    observer_thread.daemon = True
    observer_thread.start()

    watched_paths = observer

    print(f"Watching: {folder_path}")
    return reloader

def RemoveModulePathHotReload(folder_path):
    global watched_paths
    if folder_path not in watched_paths:
        return
    
    watched_paths[folder_path].stop()
    del watched_paths[folder_path]

def AddModulePath(folder_path, ignore_list={}):
    reload_scripts(folder_path, ignore_list)
