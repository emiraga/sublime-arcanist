import sublime
import sublime_plugin
import os
import subprocess
import random
import textwrap


SETTINGS_NAME = 'SublimeArcanist'
SETTINGS_FILE_NAME = '%s.sublime-settings' % SETTINGS_NAME
DIVIDER = 'SEPSublimeArcanist'+str(random.randint(1000, 9999))


def find_project_root(file_path):
    while file_path:
        if os.path.exists(os.path.join(file_path, '.arcconfig')):
            return file_path
        file_path = os.path.dirname(file_path.rstrip(os.path.sep))
    return None


def rotate(l, n):
    return l[-n:] + l[:-n]


class SublimeArcanistInlinesCommand(sublime_plugin.TextCommand):
    count = 0
    cache = {}

    def run(self, edit):
        # SublimeArcanistInlinesCommand.count

        window = sublime.active_window()
        view = window.active_view()
        project_root = find_project_root(view.file_name())

        if project_root is None:
            return
        self.project_root = project_root

        if project_root not in SublimeArcanistInlinesCommand.cache:
            cmd_args = [
                '/usr/local/bin/arc',
                'inlines',
                '--root',
                DIVIDER + project_root,
            ]
            env = os.environ
            proc = subprocess.Popen(
                cmd_args,
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            stdout, stderr = proc.communicate()
            exit = proc.wait()
            if exit != 0:
                print 'arc inline: error'
                print stdout
                print stderr
                return

            self.items = []
            for inline in stdout.split(DIVIDER):
                parts = inline.split(':', 2)
                if len(parts) != 3:
                    continue
                filepath = parts[0]
                fileline = parts[1]
                comment = parts[2]

                item = [filepath[len(project_root):] + ':' + fileline]
                for line in comment.split('\n'):
                    if line:
                        item.extend(textwrap.wrap(line, 40))
                self.items.append(item)
            SublimeArcanistInlinesCommand.cache[project_root] = self.items
        else:
            self.items = SublimeArcanistInlinesCommand.cache[project_root]

        if not self.items:
            return

        self.items = rotate(self.items, -SublimeArcanistInlinesCommand.count)

        window.show_quick_panel(
            self.items, self.select
        )

    def select(self, index):
        if index < 0 or index >= len(self.items):
            return

        window = sublime.active_window()
        path_line = self.items[index][0]
        window.open_file(
            os.path.join(self.project_root, path_line+':1'),
            sublime.ENCODED_POSITION
        )
        SublimeArcanistInlinesCommand.count += index + 1
        SublimeArcanistInlinesCommand.count %= len(self.items)
