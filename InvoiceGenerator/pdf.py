# -*- coding: utf-8 -*-
import datetime
import errno
import locale
import os
from decimal import Decimal
from pathlib import Path

from babel.dates import format_date
from babel.numbers import format_currency
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Frame, KeepInFrame, Paragraph

from InvoiceGenerator.api import Invoice
from InvoiceGenerator.conf import (
    FONT,
    FONT_BOLD_PATH,
    FONT_PATH,
    LANGUAGE,
    PATH,
    get_gettext,
)

__all__ = ["SimpleInvoice"]


def get_lang():
    return os.environ.get("INVOICE_LANG", LANGUAGE)


def _(*args, **kwargs):
    """for translations"""
    lang = get_lang()
    try:
        gettext = get_gettext(lang)
    except ImportError:

        def gettext(x):
            x

    except OSError as e:
        if e.errno == errno.ENOENT:

            def gettext(x):
                x

        else:
            raise
    return gettext(*args, **kwargs)


class BaseInvoice(object):

    def __init__(self, invoice):
        assert isinstance(
            invoice, Invoice
        ), "invoice is not instance of Invoice"

        self.invoice = invoice

    def gen(self):
        pass


class NumberedCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if num_pages > 1:
                self.draw_page_number(num_pages)
            Canvas.showPage(self)
        Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont(FONT.normal, 7)
        self.drawRightString(
            200 * mm,
            20 * mm,
            _("Page %(page_number)d of %(page_count)d")
            % {"page_number": self._pageNumber, "page_count": page_count},
        )


class CurrencyFormatter:
    def __init__(self, invoice: Invoice):
        self.invoice = invoice
        self.unit = invoice.currency
        self.locale = invoice.currency_locale

    def format(self, amount, unit=None, locale=None):
        if not unit:
            unit = self.unit
        if not locale:
            locale = self.locale
        currency_string = format_currency(amount, unit, locale=locale)
        if locale == "fr_FR.UTF-8":
            currency_string = currency_string.replace(",00", ",-")
        return currency_string


def generate_filename(invoice: Invoice):
    # path
    if not invoice.date:
        invoice.date = datetime.date.today()
    current_year = str(invoice.date.year)
    path = PATH.output_dir / current_year
    path.mkdir(parents=True, exist_ok=True)

    # invoice id
    firstletter = f"{invoice.kind[0].upper()}"
    invoice.number = len(list(path.glob("*.pdf"))) + 1
    number = f"{invoice.number:03d}"
    date = str(invoice.date).replace("-", "")
    invoice_id = f"{firstletter}{number}{date}"

    # full path
    client = invoice.client.summary.lower().replace(" ", "")
    filename = f"{invoice_id}_{client}.pdf"
    full_path = path / filename
    print(f"filename: {filename}")
    return invoice_id, full_path


class SimpleInvoice(BaseInvoice):
    """
    Generator of simple invoice in PDF format

    :param invoice: the invoice
    :type invoice: Invoice
    """

    LINE_WIDTH = 0.2
    TOP = 277
    LEFT = 15

    def gen(self):
        """
        Generate the invoice into file

        :param filename: file in which the PDF simple invoice will be written
        :type filename: string or File
        """

        pdfmetrics.registerFont(TTFont(FONT.normal, FONT_PATH))
        pdfmetrics.registerFont(TTFont(FONT.bold, FONT_BOLD_PATH))

        self.invoice_id, full_path = generate_filename(self.invoice)
        self.pdf = NumberedCanvas(str(full_path), pagesize=A4)
        self._addMetaInformation(self.pdf)

        self.pdf.setStrokeColorRGB(0, 0, 0)
        self.pdf.setLineWidth(self.LINE_WIDTH)

        self.currency = CurrencyFormatter(self.invoice)

        self._drawMain()
        self._drawTitle()
        self._drawProvider(self.TOP - 10, self.LEFT + 3)
        self._drawClient(self.TOP - 39, self.LEFT + 91)
        self._drawPayment(self.TOP - 52, self.LEFT + 2)
        self._drawDates(self.TOP - 10, self.LEFT + 91)
        self._drawObject(self.TOP - 80, self.LEFT + 3)
        items_top = 90
        ofst = self._drawItems(self.TOP - items_top, self.LEFT)
        self._drawMontantAVerserALAuteur(
            self.TOP - items_top - ofst - 15, self.LEFT
        )
        self._drawContributionDiffuseur(
            self.TOP - items_top - ofst - 45, self.LEFT
        )
        self._drawFooter(self.TOP - 265, self.LEFT - 2)
        self.pdf.setFillColorRGB(0, 0, 0)

        self.pdf.showPage()
        self.pdf.save()
        print(f"facture saved: {full_path}")

    #############################################################
    # Draw methods
    #############################################################

    def _addMetaInformation(self, pdf):
        pdf.setCreator(self.invoice.provider.summary)
        pdf.setTitle(self.invoice.title)
        pdf.setAuthor(self.invoice.creator.name)

    def _drawTitle(self):
        # Up line
        self.pdf.setFont(FONT.normal, 15)
        self.pdf.drawString(self.LEFT * mm, self.TOP * mm, self.invoice_id)
        self.pdf.drawRightString(
            (self.LEFT + 180) * mm,
            self.TOP * mm,
            _(f"n° {self.invoice_id}"),
        )

    def _drawDates(self, TOP, LEFT):
        self.pdf.setFont(FONT.normal, 10)
        top = TOP + 1
        items = []
        lang = get_lang()
        if self.invoice.date:
            items.append(
                (
                    LEFT * mm,
                    f"{_('Date de facturation')}: {format_date(self.invoice.date, locale=lang)}",
                )
            )
        if self.invoice.payback:
            items.append(
                (
                    LEFT * mm,
                    f"{_('Due date')}: {format_date(self.invoice.payback, locale=lang)}",
                )
            )
        if self.invoice.paytype:
            items.append(
                (
                    LEFT * mm,
                    f"{_('Paytype')}: {self.invoice.paytype}",
                )
            )

        for item in items:
            self.pdf.drawString(item[0], top * mm, item[1])
            top += -5

    def _drawMain(self):
        # Borders
        self.pdf.rect(
            self.LEFT * mm,
            (self.TOP - 68) * mm,
            (self.LEFT + 165) * mm,
            65 * mm,
            stroke=True,
            fill=False,
        )

        path = self.pdf.beginPath()
        path.moveTo((self.LEFT + 88) * mm, (self.TOP - 3) * mm)
        path.lineTo((self.LEFT + 88) * mm, (self.TOP - 68) * mm)
        self.pdf.drawPath(path, True, True)

        path = self.pdf.beginPath()
        path.moveTo(self.LEFT * mm, (self.TOP - 45) * mm)
        path.lineTo((self.LEFT + 88) * mm, (self.TOP - 45) * mm)
        self.pdf.drawPath(path, True, True)

        path = self.pdf.beginPath()
        path.moveTo((self.LEFT + 88) * mm, (self.TOP - 27) * mm)
        path.lineTo((self.LEFT + 180) * mm, (self.TOP - 27) * mm)
        self.pdf.drawPath(path, True, True)

    def _drawAddress(self, top, left, width, height, header_string, address):
        self.pdf.setFont(FONT.normal, 8)
        frame = Frame((left - 3) * mm, (top - 29) * mm, width * mm, height * mm)
        header = ParagraphStyle(
            "header",
            fontName=FONT.normal,
            fontSize=12,
            leading=15,
            spaceAfter=2,
        )
        default = ParagraphStyle(
            "default", fontName=FONT.normal, fontSize=8, leading=8.5
        )
        default2 = ParagraphStyle(
            "default",
            fontName=FONT.normal,
            fontSize=8,
            leading=8.5,
            spaceBefore=5,
        )
        small = ParagraphStyle("small", parent=default, fontSize=6, leading=6)
        story = [
            Paragraph(header_string, header),
            Paragraph("<br/>".join(address._get_address_lines()), default),
            Paragraph("<br/>".join(address._get_contact_lines()), default2),
            Paragraph("<br/>".join(address._get_pro_infos()), default2),
            Paragraph("<br/>".join(address.note.splitlines()), small),
        ]
        story_inframe = KeepInFrame(width * mm, height * mm, story)
        frame.addFromList([story_inframe], self.pdf)

        if address.logo_filename:
            im = Image.open(address.logo_filename)
            height = 30.0
            width = float(im.size[0]) / (float(im.size[1]) / height)
            self.pdf.drawImage(
                self.invoice.provider.logo_filename,
                (left + 84) * mm - width,
                (top - 4) * mm,
                width,
                height,
                mask="auto",
            )

    def _drawClient(self, TOP, LEFT):
        self._drawAddress(
            TOP, LEFT, 88, 41, _("Destinataire"), self.invoice.client
        )

    def _drawProvider(self, TOP, LEFT):
        self._drawAddress(
            TOP, LEFT, 88, 36, _("Émetteur"), self.invoice.provider
        )

    def _drawPayment(self, TOP, LEFT):
        self.pdf.setFont(FONT.bold, 8)
        self.pdf.drawString(
            LEFT * mm, (TOP + 2) * mm, _("Informations de paiement")
        )

        text = self.pdf.beginText((LEFT) * mm, (TOP - 2) * mm)
        lines = [
            self.invoice.provider.bank_name,
            f"{_('IBAN')} {self.invoice.provider.bank_account_str()}",
        ]
        if self.invoice.iban:
            lines.append(f"{_('IBAN')}: {self.invoice.iban}")
        if self.invoice.swift:
            lines.append(f"{_('SWIFT')}: {self.invoice.swift}")
        text.textLines(lines)
        self.pdf.drawText(text)

    def _drawObject(self, TOP, LEFT):
        self.pdf.setFont(FONT.normal, 12)
        self.pdf.drawString(
            LEFT * mm, (TOP + 2) * mm, _(f"Objet: {self.invoice.objet}")
        )

    def _drawItemsHeader(self, TOP, LEFT):
        self.pdf.setFont(FONT.normal, 12)
        self.pdf.drawString((LEFT + 3) * mm, (TOP - 5.5) * mm, _("Élements"))
        self.pdf.setFont(FONT.normal, 10)
        i = 9
        if self.invoice.mode == 1:
            self.pdf.drawString(
                (LEFT + 111) * mm,
                (TOP - i) * mm,
                _("unités"),
            )
            self.pdf.drawString(
                (LEFT + 131) * mm,
                (TOP - i) * mm,
                _("prix unitaire"),
            )
        elif self.invoice.mode == 2:
            self.pdf.drawString(
                (LEFT + 98) * mm,
                (TOP - i) * mm,
                _("droits d'auteur"),
            )
            self.pdf.drawString(
                (LEFT + 131) * mm,
                (TOP - i) * mm,
                _("prix de vente"),
            )

        self.pdf.drawRightString(
            (LEFT + 177) * mm,
            (TOP - i) * mm,
            _("total"),
        )

        i += 5
        return i

    def _drawItems(self, TOP, LEFT):
        i = self._drawItemsHeader(TOP, LEFT)
        self.pdf.setFont(FONT.normal, 7)

        for item in self.invoice.items:
            style = ParagraphStyle("normal", fontName=FONT.normal, fontSize=7)
            p = Paragraph(item.description, style)
            pwidth, pheight = p.wrapOn(self.pdf, 90 * mm, 30 * mm)
            i_add = max(float(pheight) / mm, 4.23)

            # leading line
            path = self.pdf.beginPath()
            path.moveTo(LEFT * mm, (TOP - i + 3.5) * mm)
            path.lineTo((LEFT + 180) * mm, (TOP - i + 3.5) * mm)
            self.pdf.drawPath(path, True, True)

            i += i_add
            p.drawOn(self.pdf, (LEFT + 3) * mm, (TOP - i + 3) * mm)
            i -= 4.23
            if float(int(item.count)) == item.count:
                self.pdf.drawRightString(
                    (LEFT + 118) * mm,
                    (TOP - i) * mm,
                    f"{locale.format_string('%i', item.count, grouping=True)} {item.unit}",
                )
            else:
                self.pdf.drawRightString(
                    (LEFT + 118) * mm,
                    (TOP - i) * mm,
                    f"{ locale.format_string('%.2f', item.count, grouping=True)} {item.unit}",
                )
            self.pdf.drawRightString(
                (LEFT + 148) * mm,
                (TOP - i) * mm,
                self.currency.format(item.price),
            )
            self.pdf.drawRightString(
                (LEFT + 177) * mm,
                (TOP - i) * mm,
                self.currency.format(item.total),
            )
            i += 5
        return i

    def _drawMontantAVerserALAuteur(self, TOP, LEFT):
        self.pdf.setFont(FONT.normal, 12)
        self.pdf.drawString(
            (LEFT + 3) * mm, TOP * mm, _("Montant à verser à l'auteur")
        )

        path = self.pdf.beginPath()
        path.moveTo(LEFT * mm, (TOP - 5) * mm)
        path.lineTo((LEFT + 180) * mm, (TOP - 5) * mm)
        self.pdf.drawPath(path, True, True)

        self.pdf.setFont(FONT.normal, 7)
        self.pdf.drawString(
            (LEFT + 3) * mm,
            (TOP - 9) * mm,
            _("TVA non applicable, article 293B du Code Général des impôts"),
        )

        self.pdf.setFont(FONT.bold, 11)
        self.pdf.drawRightString(
            (LEFT + 177) * mm,
            (TOP - 3) * mm,
            self.currency.format(self.invoice.price),
        )

    def _drawContributionDiffuseur(self, TOP, LEFT):
        self.pdf.setFont(FONT.normal, 12)
        self.pdf.drawString(
            (LEFT + 3) * mm,
            (TOP) * mm,
            _("Contributions dues par le diffuseur à l'URSSAF"),
        )

        path = self.pdf.beginPath()
        path.moveTo(LEFT * mm, (TOP - 5) * mm)
        path.lineTo((LEFT + 180) * mm, (TOP - 5) * mm)
        self.pdf.drawPath(path, True, True)

        self.pdf.setFont(FONT.normal, 7)
        self.pdf.drawString(
            (LEFT + 3) * mm,
            (TOP - 9) * mm,
            _("Cotisations sociales: 1% du montant brut HT"),
        )
        self.pdf.drawRightString(
            (LEFT + 177) * mm,
            (TOP - 9) * mm,
            self.currency.format(self.invoice.price * Decimal(0.10 / 100)),
        )
        self.pdf.drawString(
            (LEFT + 3) * mm,
            (TOP - 13) * mm,
            _(
                "Contribution à la formation professionnelle: 0.10% du montant brut HT"
            ),
        )
        self.pdf.drawRightString(
            (LEFT + 177) * mm,
            (TOP - 13) * mm,
            self.currency.format(self.invoice.price * Decimal(1 / 100)),
        )

        # total
        self.pdf.setFont(FONT.bold, 11)
        self.pdf.drawRightString(
            (LEFT + 177) * mm,
            (TOP - 3) * mm,
            self.currency.format(
                self.invoice.price * Decimal(0.10) / 100
                + self.invoice.price * 1 / 100
            ),
        )

    def _drawFooter(self, TOP, LEFT):
        width = 180
        height = 50
        frame = Frame(LEFT * mm, TOP * mm, width * mm, height * mm)
        title = ParagraphStyle(
            "header",
            fontName=FONT.bold,
            fontSize=7,
            spaceBefore=4,
            leading=10,
        )
        body = ParagraphStyle(
            "default", fontName=FONT.normal, fontSize=7, leading=8
        )

        text_title_1 = "En conformité de l'article L 441-6 du Code de commerce:"
        text_body_1 = "Pas d'escompte pour paiement anticipé. Règlement à faire par chèque à l'ordre de Thibault Arnoul ou par virement en date de remise de cette facture.Le paiement sera à effectuer au plus tard au trentième jour suivant la date de réception de la facture (cf: C. com. Art L. 441-6, al.2 modifié de la loi du 15 mai 2001). Tout règlement effectué après expiration de ce délai donnera lieu à une pénalité fixée à 15% du montant total de la facture, par mois de retard entamé, exigible sans rappel le jour suivant la date limite du réglement, ainsi qu'à une indemnité forfaitaire pour frais de recouvrement d'un montant de 40€. Mention obligatoire. Lutte contre les retards de paiement / Art. 53, loi NRE."

        text_title_2 = "Informations concernant l'URSSAF:"
        text_body_2 = "Conformément à l'article L382-4 du Code de la Sécurité Sociale et L6331-65 du Code du Travail, le client doit s'acquitter d'une contribution personnelle de 1,1% de la rémunération brute hors taxes directement auprès de l'URSSAF (anciennement AGESSA).https://www.artistes-auteurs.urssaf.fr/."

        text_title_3 = "Informations concernant les droits d'exploitation:"
        text_body_3 = "Thibault Arnoul ne cède que les droits d'exploitation de la création limités aux termes du présent document. Thibault Arnoul reste propriétaire de l'intégralité des créations tant que la prestation n'est pas entièrement réglée.Toute utilisation sortant du cadre initialement prévu dans ce devis est interdite; sauf autorisation expresse et écrite de Thibault Arnoul."

        story = [
            Paragraph(text_title_1, title),
            Paragraph(text_body_1, body),
            Paragraph(text_title_2, title),
            Paragraph(text_body_2, body),
            Paragraph(text_title_3, title),
            Paragraph(text_body_3, body),
        ]
        story_inframe = KeepInFrame(width * mm, height * mm, story)
        frame.addFromList([story_inframe], self.pdf)
