import pytest
from core_v1.app.monetizze_catalog import CatalogError, MonetizzeCatalogClient, normalize_products


def example():
    # Structural fixture based on the official /myproducts documentation, not market data.
    return {'status':200,'totalRegistros':1,'dados':[{'codigo':'34348','nome':'Curso básico de php',
        'status':'2','planos':[{'codigo':'265839','nome':'Plano Mensal','status':'1','valor':'99.00'},
                             {'codigo':'362565','nome':'Plano Antigo','status':'0','valor':'79.00'}]}]}


def test_active_plans_are_not_publication_permission():
    result=normalize_products(example())[0]
    assert len(result['planos_ativos'])==1
    assert result['publication_authorized'] is False
    assert result['membership_verified'] is False
    assert result['affiliate_link_verified'] is False
    assert 'chave' not in result


@pytest.mark.parametrize('payload',[None,{}, {'status':403,'dados':[]},
    {'status':200,'dados':[],'totalRegistros':1},
    {'status':200,'dados':[{}],'totalRegistros':1}])
def test_rejects_malformed_or_incomplete_catalog(payload):
    with pytest.raises(CatalogError): normalize_products(payload)


def test_duplicate_product_fails_instead_of_fabricating_count():
    payload=example();payload['dados']*=2;payload['totalRegistros']=2
    with pytest.raises(CatalogError): normalize_products(payload)


def test_client_uses_documented_read_only_scope_and_headers(monkeypatch):
    client=MonetizzeCatalogClient('test-only-consumer-key')
    calls=[]
    def get(path,headers):
        calls.append((path,headers))
        return {'TOKEN':'test-only-temporary-token'} if path=='/token' else example()
    monkeypatch.setattr(client,'_get',get)
    assert len(client.products())==1
    assert calls==[('/token',{'X_CONSUMER_KEY':'test-only-consumer-key'}),
        ('/myproducts?retorno_produtor=0&retornar_produtos_aprovacao=0',{'TOKEN':'test-only-temporary-token'})]


def test_no_redirect_with_credentials():
    from core_v1.app.monetizze_catalog import _NoRedirect
    with pytest.raises(CatalogError):
        _NoRedirect().redirect_request(None,None,302,'',{},'https://elsewhere.invalid')
