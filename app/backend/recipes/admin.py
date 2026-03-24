from datetime import datetime

from flask_login import current_user

from backend.utils.admin.views import ProtectedModelView


class RecipeView(ProtectedModelView):
    can_view_details = True
    column_list = ['name', 'author.name', 'meal_type.name', 'like_count', 'description',
                   'is_published', 'is_visible', 'created_on', 'last_upated', 'published_on']
    
    column_searchable_list = ['name', 'author.name', 'created_on', 'published_on', 'last_updated', 'description']
    
    form_columns = ['name', 'slug', 'author', 'meal_type', 'tags', 'description', 'ingredients', 'text',
                    'cooking_time', 'calories', 'is_published', 'is_visible', 'created_on', 'last_updated',
                    'published_on', 'applications']
    
    form_widget_args = {
        "applications": {
            'readonly': True,
            'style': 'cursor: not-allowed;'
        }
    }
    

class ApplicationView(ProtectedModelView):
    column_list = ['recipe.name', 'recipe.author.name', 'status', 'created_on']
    column_choices = {
        'status': [
            (0, 'Not Reviewed'),
            (1, 'Accepted'),
            (2, 'Declined')
        ]
    }
    
    form_choices = {
        'status': [
            (0, 'Not Reviewed'),
            (1, 'Accepted'),
            (2, 'Declined')
        ]
    }
    
    form_columns = ['recipe', 'comment', 'created_on', 'last_reviewed_by', 'status']
    
    form_widget_args = {
        "recipe": {
            'readonly': True, 
            'style': 'cursor: not-allowed;'
        },
        "comment": {
            'readonly': True, 'disabled': True
        },
        "created_on": {
            'readonly': True, 'disabled': True
        },
        "last_reviewed_by": {
            'readonly': True, 'disabled': True
        },
    }
    
    
    def on_model_change(self, form, model, is_created):
        if is_created == False: 
            if form.data['status'] == '1':
                # If approved
                model.recipe.is_published = True
                model.recipe.published_on = datetime.now()
            
            model.last_reviewed_by_id = current_user.id
        
        return super().on_model_change(form, model, is_created)