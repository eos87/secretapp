from contrib.forms import UserContentForm

def DiscussionForm(UserContentForm):
    class Meta:
        model = Discussion
        fields = ('title', 'text',)