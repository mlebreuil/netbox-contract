from django.utils.translation import gettext_lazy as _
from netbox.object_actions import ObjectAction

AMEND_PERMISSION = 'netbox_contract.amend_contractline'


def can_amend(line, user):
    """Whether the user may amend this line now: the line is amendable and the amend permission covers it."""
    return line.can_be_amended and user.has_perm(AMEND_PERMISSION, line)


class AmendContractLine(ObjectAction):
    """
    Amend the price or quantity of an invoiced contract line (research D6). NetBox drops the button for users without
    any amend permission; render() also hides it for lines that cannot be amended or that the user's amend permission
    constraints do not cover.
    """

    name = 'amend'
    label = _('Amend')
    permissions_required = {'amend'}
    url_kwargs = ['pk']
    template_name = 'netbox_contract/buttons/amend.html'

    @classmethod
    def render(cls, context, obj, **kwargs):
        if not can_amend(obj, context['request'].user):
            return ''
        return super().render(context, obj, **kwargs)
