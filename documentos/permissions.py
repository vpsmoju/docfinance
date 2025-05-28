from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(
            self.request, "Apenas administradores podem acessar esta página."
        )
        return redirect("documento_list")


class AdminOrOwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_staff
            or self.get_object().baixado_por == self.request.user
        )
