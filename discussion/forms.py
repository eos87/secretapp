from django import forms
from django.core.urlresolvers import reverse
from perm.forms import UserContentForm
from utilz.search import SearchForm
from models import *

SORT_ORDERS = (
                ('updated desc', 'Activity'),
                ('created desc', 'Newest'),
                ('comments desc', 'Most Posts'),
                ('secrets desc', 'Most Secrets'),
            )

class DiscussionSearchForm(SearchForm):
    # sort
    sort    = forms.ChoiceField(choices=SORT_ORDERS, required=False)
    
    # text searches
    title   = forms.CharField(required=False)
    text    = forms.CharField(required=False)
    
    class Meta(SearchForm.Meta):
        model = Discussion
        url_name = 'search_discussions'
        results_per_page = 20
        default_sort = SORT_ORDERS[0][0]
        cheeky = False
    
    def save(self):
        # build vars
        data = self.cleaned_data
        queries = [self.base_query]
        
        # searching only the title field
        if 'title' in data and data['title']:
            queries.append("(title:(%s)^3 OR title:(%s*))" % (data['title'], data['title']))
        
        # searching for any text
        if 'text' in data and data['text']:
            queries.append("(title:(%s)^10 OR text:(%s)^3 OR blob:(%s))"\
                            % (data['text'], data['text'], data['text']))
        # return
        return self.get_results(" AND ".join(queries))


class DiscussionForm(UserContentForm):
    tags = forms.CharField(required=False, widget=forms.TextInput)
    class Meta:
        model = Discussion
        fields = ('title', 'text', 'tags')
    
    def set_url(self, new=True):
        if new:
            self.action_url = reverse('new_discussion')
        return self



