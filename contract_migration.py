from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from netbox_contract.models import ContractAssignement, Contract

for contract in Contract.objects.all():
    circuits = contract.circuit.all()
    for circuit in circuits:
        try :
            circuit_type = ContentType.objects.get_for_model(circuit).id
            assignement = ContractAssignement.objects.get(content_type=circuit_type, object_id= circuit.id, contract__id=contract.id)
        except ObjectDoesNotExist:
            assignement = ContractAssignement(content_object=circuit, contract=contract)
            assignement.save()
