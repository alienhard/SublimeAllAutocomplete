# Extend Sublime Text 2 autocompletion to find matches in all open
# files of the current window. By default, Sublime only considers
# words from the current file.

import sublime_plugin
import sublime


class AllAutocomplete(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        words = set()
        views = [v for v in sublime.active_window().views() if v.id() != view.id()]
        for v in views:
            words.update(v.extract_completions(prefix))
        matches = [(w, w) for w in words]
        return matches
