# -*- coding: utf-8 -*-
from InvoiceGenerator.api import Client, Creator, Invoice, Item, Provider
from InvoiceGenerator.pdf import SimpleInvoice

client = Client(
    "Ets",  # entreprise
    additional_name="additional name",
    address="Adresse",
    city="ville",
    zip_code="code postal",
    country="France",
    phone="06",
    email="@",
    bank_name="",
    bank_account="",
    note="",
)

provider = Provider(
    "prénom nom",
    address="rue",
    city="city",
    zip_code="zip",
    country="France",
    phone="tel",
    email="mail",
    bank_name="bankname",
    bank_account="iban",
    ss="n° de sécu",
    siret="n° siret",
)

creator = Creator("nom prénom")

invoice = Invoice(client, provider, creator)#, title="Facture")
invoice.add_item(Item(32, 600, description="Item 1"))
invoice.add_item(Item(60, 50, description="Item 2", tax=21))
invoice.add_item(Item(50, 60, description="Item 3", tax=0))
invoice.add_item(Item(5, 600, description="Item 4", tax=15))
invoice.objet = "Vente de droits sur blblabla"
invoice.mode = 2

SimpleInvoice(invoice).gen()
