# Extend Sublime Text 2 autocompletion to find matches in all open
# files of the current window. By default, Sublime only considers
# words from the current file.

import sublime_plugin
import sublime


class AllAutocomplete(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        words = set()
        views = [v for v in sublime.active_window().views()]
        for v in views:
            #Extract this view's words
            view_words = v.extract_completions(prefix)
            #Work around truncation bug
            view_words = fix_truncation(v, view_words)
            #Add the words to the set
            words.update(view_words)
        matches = [(w, w) for w in words]
        return matches

# Workaround for truncation bug when using view.extract_completions in some types of files
def fix_truncation(view, words):
    fixed_words = set()
    for w in words:
        #The word is truncated if and only if it cannot be found with a word boundary before and after
        truncated = view.find(r'\b' + w + r'\b', 0) is None
        if truncated:
            #Truncation is always by a single character, so we extend the word by one word character before a word boundary
            extended_words = []
            view.find_all(r'\b' + w + r'\w\b', 0, "$0", extended_words)
            fixed_words.update(extended_words)
        else:
            #Pass through non-truncated words
            fixed_words.add(w)
    return fixed_words
