# Extends Sublime Text autocompletion to find matches in all open
# files. By default, Sublime only considers words from the current file.

import sublime_plugin
import sublime
import re
import time
import datetime
import os
from os.path import basename

# Import the debugger
from python_debug_tools import Debugger

# Debugger settings: 0 - disabled, 127 - enabled
log = Debugger( 1, os.path.basename( __file__ ) )


# limits to prevent bogging down the system
MIN_WORD_SIZE = 3
MAX_WORD_SIZE = 50

MAX_VIEWS = 20
MAX_WORDS_PER_VIEW = 100
MAX_FIX_TIME_SECS_PER_VIEW = 0.01


def plugin_unloaded():
    g_settings.clear_on_change('All Autocomplete')


def plugin_loaded():
    on_settings_modified();
    g_settings.add_on_change('All Autocomplete', on_settings_modified)


def on_settings_modified():
    log( 2, "on_settings_modified" )

    global g_settings
    g_settings = sublime.load_settings('All Autocomplete.sublime-settings')


class AllAutocomplete(sublime_plugin.EventListener):

    def on_query_completions( self, active_view, prefix, locations ):
        # log( 16, "AMXXEditor::on_query_completions(4)" )

        view_words = None
        words_list = []
        start_time = time.time()

        if len( locations ) > 0:
            view_words = active_view.extract_completions( prefix, locations[0] )

        else:
            view_words = active_view.extract_completions( prefix )

        view_words = fix_truncation( active_view, view_words )

        for word in view_words:
            # Remove the annoying `(` on the string
            word = word.replace('$', '\\$').split('(')[0]

            if word not in words_list:
                words_list.append( ( word, word ) )

            if time.time() - start_time > 0.05:
                break

        # log( 16, "( on_query_completions ) Current views loop took: %f" % ( time.time() - start_time ) )
        buffers_id_set = set()
        view_base_name = None

        # Limit number of views but always include the active view. This
        # view goes first to prioritize matches close to cursor position.
        views = sublime.active_window().views()
        buffers_id_set.add( active_view.buffer_id() )

        for view in views:
            view_buffer_id = view.buffer_id()
            # log( 16, "( on_query_completions ) view: %d" % view.id() )
            # log( 16, "( on_query_completions ) buffers_id: %d" % view_buffer_id )
            # log( 16, "( on_query_completions ) buffers_id_set size: %d" % len( buffers_id_set ) )

            if view_buffer_id not in buffers_id_set:
                buffers_id_set.add( view_buffer_id )

                view_words     = view.extract_completions(prefix)
                view_words     = fix_truncation(view, view_words)
                view_base_name = view.file_name()

                if view_base_name is None:
                    view_base_name = ""

                else:
                    view_base_name = os.path.basename( view_base_name )

                for word in view_words:
                    # Remove the annoying `(` on the string
                    word = word.replace('$', '\\$').split('(')[0]

                    if word not in words_list:
                        # log( 16, "( on_query_completions ) word: %s" % word )
                        words_list.append( ( word + ' \t' + view_base_name, word ) )

                    if time.time() - start_time > 0.3:
                        # log( 16, "( on_query_completions ) Breaking all views loop after: %f" % time.time() - start_time )
                        return words_list

        # log( 16, "( on_query_completions ) All views loop took: %f" % ( time.time() - start_time ) )
        return words_list


def is_disabled_in(scope):
    excluded_scopes = g_settings.get("exclude_from_completion", [])

    for excluded_scope in excluded_scopes:

        if scope.find(excluded_scope) != -1:
            return True

    return False


def filter_words(words):
    words = words[0:MAX_WORDS_PER_VIEW]
    return [w for w in words if MIN_WORD_SIZE <= len(w) <= MAX_WORD_SIZE]


# keeps first instance of every word and retains the original order
# (n^2 but should not be a problem as len(words) <= MAX_VIEWS*MAX_WORDS_PER_VIEW)
def without_duplicates(words):
    result = []
    used_words = []

    for w, v in words:

        if w not in used_words:
            used_words.append(w)
            result.append((w, v))

    return result


# Ugly workaround for truncation bug in Sublime when using view.extract_completions()
# in some types of files.
def fix_truncation(view, words):
    fixed_words = []
    start_time = time.time()

    for i, w in enumerate(words):
        #The word is truncated if and only if it cannot be found with a word boundary before and after

        # this fails to match strings with trailing non-alpha chars, like
        # 'foo?' or 'bar!', which are common for instance in Ruby.
        match = view.find(r'\b' + re.escape(w) + r'\b', 0)
        truncated = is_empty_match(match)

        if truncated:
            #Truncation is always by a single character, so we extend the word by one word character before a word boundary
            extended_words = []
            view.find_all(r'\b' + re.escape(w) + r'\w\b', 0, "$0", extended_words)

            if len(extended_words) > 0:
                fixed_words += extended_words

            else:
                # to compensate for the missing match problem mentioned above, just
                # use the old word if we didn't find any extended matches
                fixed_words.append(w)
        else:
            #Pass through non-truncated words
            fixed_words.append(w)

        # if too much time is spent in here, bail out,
        # and don't bother fixing the remaining words
        if time.time() - start_time > MAX_FIX_TIME_SECS_PER_VIEW:
            return fixed_words + words[i+1:]

    return fixed_words


if sublime.version() >= '3000':

    def is_empty_match(match):
        return match.empty()

else:
    plugin_loaded()

    def is_empty_match(match):
        return match is None

