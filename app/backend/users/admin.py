from backend.utils.admin.views import ProtectedModelView


class UserView(ProtectedModelView):
    can_create = False
    form_columns = ['name', 'bio', 'email',  'created_on', 'is_superuser', 'is_active', 'profile_picture', 'reviewed_applications']

    column_list = ['name', 'created_on', 'recipe_count', 'like_count', 'is_superuser', 'is_active']
    column_searchable_list = ['name', 'created_on']
    
    can_view_details = True
    column_details_exclude_list = ['password']