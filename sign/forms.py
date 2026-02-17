from allauth.account.forms import SignupForm
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist

class CommonSignupForm(SignupForm):

    def save(self, request):
        user = super().save(request)
        try:
            common_group = Group.objects.get(name='common')
            common_group.user_set.add(user)
        except ObjectDoesNotExist:
            # Логируем или просто пропускаем — группа не найдена
            pass
        return user

