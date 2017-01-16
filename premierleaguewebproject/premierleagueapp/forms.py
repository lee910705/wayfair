from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import validate_email, RegexValidator
from premierleagueapp.models import *

class RegistrationForm(forms.ModelForm):
    username   = forms.CharField(max_length = 20,
                                 validators = [RegexValidator(r'^[0-9a-zA-Z]*$',
                                                              message='Enter only letters and numbers')])
    email      = forms.CharField(max_length = 40,
                                 validators = [validate_email])
    password1 = forms.CharField(max_length = 200, 
                                label='Password', 
                                widget = forms.PasswordInput())
    password2 = forms.CharField(max_length = 200, 
                                label='Confirm password',  
                                widget = forms.PasswordInput())
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
        return user

    # Customizes form validation for properties that apply to more
    # than one field.  Overrides the forms.Form.clean function.
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super(RegistrationForm, self).clean()
        
        # Confirms that the two password fields match
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match.")

        # Generally return the cleaned data we got from our parent.
        return cleaned_data


    # Customizes form validation for the username field.
    def clean_username(self):
        # Confirms that the username is not already present in the
        # User model database.
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError("Username is already taken.")

        # Generally return the cleaned data we got from the cleaned_data
        # dictionary
        return username

class WeatherForm(forms.Form):
    city = forms.CharField(max_length=40)

    def clean(self):
        cleaned_data = super(WeatherForm, self).clean()
        city = cleaned_data.get('city')
        if city == "":
            raise forms.ValidationError("Must type something in city")
        return cleaned_data

class EditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")
