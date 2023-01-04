from extras.plugins import PluginTemplateExtension
from .models import Contract
from . import tables

class CircuitContracts(PluginTemplateExtension):
    model = 'circuits.circuit'

    def full_width_page(self):
        circuit = self.context['object']
        table = tables.ContractListBottomTable(circuit.contracts.all())
        table.configure(self.context['request'])

        return self.render('contract_list_bottom.html', extra_context={
            'contracts_table': table,
        })

template_extensions = [CircuitContracts]