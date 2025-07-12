# -*- coding: utf-8 -*-

import collections
import decimal
from decimal import Decimal

from InvoiceGenerator.conf import _

__all__ = ["Address", "Client", "Provider", "Creator", "Item", "Invoice"]


class UnicodeProperty(object):
    _attrs = ()

    def __setattr__(self, key, value):
        if key in self._attrs:
            value = value
        self.__dict__[key] = value


class Address(UnicodeProperty):
    """
    Abstract address definition

    :param summary: address header line - name of addressee or company name
    :param additional_name: client name
    :param address: line of the address with street and house number
    :param city: city or part of the city
    :param zip_code: zip code (PSČ in Czech)
    :param phone:
    :param email:
    :param bank_name:
    :param bank_account: bank account number
    :param bank_code:
    :param note: note that will be written on the invoice
    :param vat_id: value added tax identification number (DIČ in czech)
    :param vat_note: VAT note
    :param ir: Taxpayer identification Number (IČO in czech)
    :param logo_filename: path to the image of logo of the company
    :param country: country
    :param ss: numéro de sécurité sociale
    :param siret: numéro siret
    """

    _attrs = (
        "summary",
        "additional_name",
        "address",
        "city",
        "zip_code",
        "phone",
        "email",
        "bank_name",
        "bank_account",
        "bank_code",
        "note",
        "vat_id",
        "ir",
        "logo_filename",
        "vat_note",
        "country",
        "ss",
        "siret",
    )

    def __init__(
        self,
        summary,
        additional_name="",
        address="",
        city="",
        zip_code="",
        phone="",
        email="",
        bank_name="",
        bank_account="",
        bank_code="",
        note="",
        vat_id="",
        ir="",
        logo_filename="",
        vat_note="",
        country="",
        ss="",
        siret="",
    ):
        self.summary = summary
        self.address = address
        self.additional_name = additional_name
        self.city = city
        self.country = country
        self.zip_code = zip_code
        self.phone = phone
        self.email = email
        self.bank_name = bank_name
        self.bank_account = bank_account
        self.bank_code = bank_code
        self.note = note
        self.vat_id = vat_id
        self.vat_note = vat_note
        self.ir = ir
        self.logo_filename = logo_filename
        self.ss = ss
        self.siret = siret

    def bank_account_str(self):
        """Returns bank account identifier with bank code after slash"""
        if self.bank_code:
            return "%s/%s" % (self.bank_account, self.bank_code)
        else:
            return self.bank_account

    def _get_address_lines(self):
        address_line = [self.summary]
        if self.additional_name:
            address_line.append(self.additional_name)
        address_line += [
            self.address,
            " ".join(filter(None, (self.zip_code, self.city))),
        ]
        if self.country:
            address_line.append(self.country)
        if self.vat_id:
            address_line.append(_("Vat in: %s") % self.vat_id)

        if self.ir:
            address_line.append(_("IR: %s") % self.ir)

        return address_line

    def _get_contact_lines(self):
        return [
            self.phone,
            self.email,
        ]

    def _get_pro_infos(self):
        siret = ss = ""
        if self.siret:
            siret = f"SIRET: {self.siret}"
        if self.ss:
            ss = f"SS: {self.ss}"
        return [siret, ss]


class Client(Address):
    """
    Definition of client (recipient of the invoice) address.
    """

    pass


class Provider(Address):
    """
    Definition of prvider (subject, that issued the invoice) address.
    """

    pass


class Creator(UnicodeProperty):
    """
    Definition of creator of the invoice (ussually an accountant).

    :param name: name of the issuer
    :param stamp_filename: path to file with stamp (or subscription)
    """

    _attrs = ("name", "stamp_filename")

    def __init__(self, name, stamp_filename=""):
        self.name = name
        self.stamp_filename = stamp_filename


class Item(object):
    """
    Item on the invoice.

    :param count: number of items or quantity associated with unit
    :param price: price for unit
    :param unit: unit in which it is measured (pieces, Kg, l)
    :param tax: the tax rate under which the item falls (in percent)
    """

    def __init__(self, count, price, description="", unit="", tax=Decimal(0)):
        self.count = count
        self.price = price
        self._description = description
        self.unit = unit
        self.tax = tax

    @property
    def total(self):
        """Total price for the items without tax."""
        return self.price * self.count

    @property
    def total_tax(self):
        """Total price for the items with tax."""
        return self.price * self.count * (Decimal(1) + self.tax / Decimal(100))

    def count_tax(self):
        """Value of only tax that will be payed for the items."""
        return self.total_tax - self.total

    @property
    def description(self):
        """Short description of the item."""
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def count(self):
        """Count or amount of the items."""
        return self._count

    @count.setter
    def count(self, value):
        if value:
            self._count = Decimal(value)

    @property
    def price(self):
        """Price for unit."""
        return self._price

    @price.setter
    def price(self, value):
        if value:
            self._price = Decimal(value)

    @property
    def unit(self):
        """Unit."""
        return self._unit

    @unit.setter
    def unit(self, value):
        if value:
            self._unit = value

    @property
    def tax(self):
        """Tax rate."""
        return self._tax

    @tax.setter
    def tax(self, value):
        if value is None:
            self._tax = Decimal(0)
        else:
            self._tax = Decimal(value)


class Invoice(UnicodeProperty):
    """
    Invoice definition

    :param client: client of the invoice
    :type client: Client
    :param creator: creator of the invoice
    :type creator: Creator
    :param provider: provider of the invoice
    :type provider: Provider
    """

    kind = "facture"  # facture|devis use set_kind()
    #: mode: 1|2, type d'items
    # 1: unités, prix unitaire, total
    # 2: prix de vente, droits d'auteur (%), total
    mode = 1  #: textual description of type of payment
    paytype = None
    #: number or string used as the invoice identifier
    number = None
    iban = None
    swift = None
    #: date of exposure
    date = None
    #: due date
    payback = None
    #:  taxable date
    taxable_date = None
    #: currency_locale: locale according to which will be the written currency representations
    currency_locale = "fr_FR.UTF-8"
    #: currency identifier (e.g. "$" or "Kč")
    currency = "€"

    # objet de la facture
    objet = ""

    #: round result to integers?
    rounding_result = False

    #: Result rounding strategy (identifiers from `decimal` module).
    #: Default strategy for rounding in Python is bankers' rounding,
    #: which means that half of the X.5 numbers are rounded down and half up.
    #: Use this parameter to set different rounding strategy.
    rounding_strategy = decimal.ROUND_HALF_EVEN

    def __init__(self, client, provider, creator):
        assert isinstance(client, Client)
        assert isinstance(provider, Provider)
        assert isinstance(creator, Creator)

        self.client = client
        self.provider = provider
        self.creator = creator
        self._items = []

        for attr in self._attrs:
            self.__setattr__(attr, "")

    def _price_tax_unrounded(self):
        return sum(item.total_tax for item in self.items)

    @property
    def price(self):
        """Total sum price without taxes."""
        return self._round_result(sum(item.total for item in self.items))

    @property
    def price_tax(self):
        """Total sum price including taxes."""
        return self._round_result(self._price_tax_unrounded())

    def set_kind(self, kind):
        possible_values = ["facture", "devis"]
        if kind in possible_values:
            self.kind = kind
        else:
            print(f"wrong kind: '{kind}'. Possible values: {possible_values}")
            self.kind = possible_values[0]

    def set_mode(self, mode):
        possible_values = [1, 2]
        if mode in possible_values:
            self.mode = mode
        else:
            print(f"wrong mode: '{mode}'. Possible values: {possible_values}")
            self.mode = possible_values[0]

    def add_item(self, item):
        """
        Add item to the invoice.

        :param item: the new item
        :type item: Item class
        """
        assert isinstance(item, Item)
        self._items.append(item)

    @property
    def items(self):
        """Items on the invoice."""
        return self._items

    def _round_price(self, price):
        return decimal.Decimal(price).quantize(
            0, rounding=self.rounding_strategy
        )

    @property
    def difference_in_rounding(self):
        """Difference between rounded price and real price."""
        price = self._price_tax_unrounded()
        return Decimal(self._round_price(price)) - price

    def _get_grouped_items_by_tax(self):
        table = collections.OrderedDict()
        for item in self.items:
            if item.tax not in table:
                table[item.tax] = {
                    "total": item.total,
                    "total_tax": item.total_tax,
                    "tax": item.count_tax(),
                }
            else:
                table[item.tax]["total"] += item.total
                table[item.tax]["total_tax"] += item.total_tax
                table[item.tax]["tax"] += item.count_tax()

        return table

    def _round_result(self, price):
        if self.rounding_result:
            return self._round_price(price)
        return price

    def generate_breakdown_vat(self):
        return self._get_grouped_items_by_tax()

    def generate_breakdown_vat_table(self):
        rows = []
        for vat, items in self.generate_breakdown_vat().items():
            rows.append((vat, items["total"], items["total_tax"], items["tax"]))

        return rows
