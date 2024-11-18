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
    "Thibault Arnoul",
    address="40 rue Oberlin",
    city="Strasbourg",
    zip_code="67000",
    country="France",
    phone="+33695736895",
    email="thibault.assiste.par.ordinateur@proton.me",
    bank_name="Boursobank",
    bank_account="FR76 4061 8803 6000 0408 3444 612",
    ss="1922077728837775",
    siret="830 459 533 00014",
)

creator = Creator("Thibault Arnoul")

invoice = Invoice(client, provider, creator, title="Facture")
invoice.add_item(Item(32, 600, description="Item 1"))
invoice.add_item(Item(60, 50, description="Item 2", tax=21))
invoice.add_item(Item(50, 60, description="Item 3", tax=0))
invoice.add_item(Item(5, 600, description="Item 4", tax=15))
invoice.objet = "Vente de droits sur blblabla"
invoice.mode = 2


SimpleInvoice(invoice).gen()
