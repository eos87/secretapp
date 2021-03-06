from django import forms
from django.core.urlresolvers import reverse
from discussion.models import Discussion
from perm.forms import UserContentForm
from utilz.search import SearchForm
from models import *


# When adding to this list.
#   1. Need to add template
#   2. Need to update solr schema (incl restart)
#   3. Need to reindex solr
SECRET_RENDER_TEMPLATES = ('list', 'photo', 'location')
SECRET_RENDER_FOLDER = 'secret/render/%s.html'

SORT_ORDER = (
                ('score desc', 'Most Relevant'),
                ('created desc', 'Newest'),
                ('created asc', 'Oldest')
            )

SORT_MAPPING = {'relevance':'score desc', 'latest':'created desc', 'popular':'comments desc', 'undiscovered':"comments asc" }

  
USER_SORT_ORDER = (
                ('relevance', 'Most Relevant'),
                ('latest', 'Latest'),
                #('popular', 'Popular'),
                #('undiscovered', 'Undiscovered'),
            )
            
class SecretSearchForm(SearchForm):
    # choose a template
    templates   = SECRET_RENDER_TEMPLATES
    template    = forms.ChoiceField(choices=[(s,s) for s in SECRET_RENDER_TEMPLATES], required=False)
    
    # sort
    sort        = forms.ChoiceField(choices=SORT_ORDER, required=False)
    usort   = forms.ChoiceField(choices=USER_SORT_ORDER, required=False)
    
    # text
    title       = forms.CharField(required=False)
    text        = forms.CharField(required=False)
    
    # location (maps)
    location_fields = ('north', 'south', 'east', 'west')
    location    = forms.CharField(required=False)
    south       = forms.FloatField(required=False)
    north       = forms.FloatField(required=False)
    west        = forms.FloatField(required=False)
    east        = forms.FloatField(required=False)
    
    class Meta(SearchForm.Meta):
        model = Secret
        url_name = 'search_secrets'
        default_template = 'list'
        default_sort = SORT_ORDER[0][0]
        results_per_page = 10
    
    def clean_sort(self):
        data = self.cleaned_data['sort']
        if 'usort' in self.data:
            usort = self.data['usort']
            if usort in SORT_MAPPING:
                data = SORT_MAPPING[usort]
            else:
                data = self.Meta.default_sort
        return data
    
    def template_url(self, template):
        """ Returns the url to change the template but keep the same search critieon """
        q = self.Meta.query_dict.copy()
        q['template'] = template
        return "?%s" % q.urlencode()
    
    def get_available_sort_orders(self):
        return USER_SORT_ORDER
        
    def save(self):
        # build vars
        data = self.cleaned_data
        queries = [self.base_query]
        
        # searching only the title field
        if 'title' in data and data['title']:
            # Turns "Cemetery in soh" -> "+(Cemetery Cemetery*) +(in in*) +(soh soh*)"
            #plus_title = ' '.join(['+(%s* %s)' % (x, x) for x in data['title'].split(' ')])
            #queries.append("(title:(%s))" % plus_title)
            queries.append("(title:(%s))" % data['title'])
        
        # searching any text field's (may extend to comments)
        if 'text' in data and data['text']:
            text = data['text']
            queries.append("(title:(%s)^2 OR location:(%s) OR description:(%s))"\
                                                                % (text, text, text))
        
        # searching any text field's (may extend to comments)
        if 'location' in data and data['location']:
            location = data['location']
            queries.append("(location:(%s) OR description:(%s))" % (location, location))
        
        # do quick check has all fields (ugly)
        if 'south' in data and data['south'] \
            and 'north' in data and data['north'] \
                and 'west' in data and data['west'] \
                    and 'east' in data and data['east']:
            queries.append("(latitude:[%s TO %s] AND longitude:[%s TO %s])"\
            % (data['south'], data['north'], data['west'], data['east']))
        
        # if on photo view, only show secrets with photos
        if hasattr(self, 'chosen_template') and self.chosen_template == 'photo':
            queries.append("(photocount:[1 TO *])")
            self.Meta.results_per_page = 24
        
        # return
        return self.get_results(" AND ".join(queries))



class SecretForm(UserContentForm):
    title = forms.CharField(label="Secret")
    url = forms.URLField(label="Website", required=False)
    secrets = forms.IntegerField(required=False)
    image = forms.ImageField(required=False)
    class Meta:
        model = Secret
        fields = ('title', 'location', 'latitude', 'longitude', 'description', 'url', 'google_reff')
        id = 'secret'
    
    def save(self, request):        
        is_existing_secret = False
        if self.cleaned_data['secrets']:
            #adding something to an existing secret
            try:
                the_secret = Secret.viewable.get(pk=self.cleaned_data['secrets'])
            except:
                the_secret = None   
            is_existing_secret = True
        else:        
            #adding a brand new secret
            the_secret = super(SecretForm, self).save(request)
            the_secret.save()
        
        if not the_secret is None:
            if self.cleaned_data['image']:
                from photo.models import UploadedPhoto
                new_photo = UploadedPhoto(secret=the_secret, created_by=request.user)
                new_photo.caption = self.cleaned_data['description']
                new_photo.save()
                try:
                    new_photo.save_files(self.cleaned_data['image'])
                except:
                    # If save fails, delete image
                    new_photo.deleted = True
                    new_photo.save()
                the_secret.save()
            elif self.cleaned_data['description']:
                from comment.models import SecretComment
                new_comment = SecretComment(secret=the_secret, created_by=request.user)
                new_comment.text = self.cleaned_data['description']
                new_comment.save()           
                the_secret.save()
        return the_secret
    
    def set_url(self, secret=None):
        # handling data input
        if hasattr(secret, 'pk') and secret.pk:
            secret_id = secret.pk
        else:
            secret_id = None
        
        # handle options
        if secret_id:
            self.action_url = reverse('edit_secret', kwargs={'pk': secret_id })
        else:
            self.action_url = reverse('new_secret')
        return self