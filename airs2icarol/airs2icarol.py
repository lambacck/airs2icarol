# -*- coding: utf-8 -*-
from collections import namedtuple
from functools import partial
from zipfile import ZipFile
import zipfile
import codecs
import tempfile
import itertools
import os


from lxml import etree

from . import bufferedzip
from .utf8csv import UTF8CSVWriter

FieldMapping = namedtuple('FieldMapping', 'FieldID FieldName extractfn')


def open_zipfile(dest_file):
    if dest_file.endswith('.zip'):
        try:
            zip = ZipFile(dest_file, 'r')
            files = zip.namelist()
            return zip.open(files[0], 'r')
        except zipfile.BadZipfile:
            pass

    return open(dest_file)


def _convert_part(error_log, processed, iterable, root, tagname, culture=None, agencynum=None, _=None):
    key = None
    subagency_num = None
    to_remove = []
    while True:
        try:
            event, element = next(iterable)
        except StopIteration:
            return

        if event == 'start' and element.tag in airs_type_mapping:
            to_remove.append(element)

            for row in _convert_part(error_log, processed, iterable, element, element.tag, culture, subagency_num or agencynum, _):
                yield row

        elif event == 'end' and element.tag == 'Key' and element.getparent() == root:
            key = element.text
            if tagname == 'Agency':
                subagency_num = key

        elif event == 'end' and element == root:
            # print 'found end'
            for el in to_remove:
                root.remove(el)
            oldtag = element.tag

            if oldtag == 'Source':
                return

            record_type = _tag_to_type_map.get(tagname)
            record_id = (record_type, agencynum, key)
            if record_id in processed:
                return

            processed.add(record_id)
            joinstr = _(u'; ')
            for mapping in airs_type_mapping[tagname]:
                value = mapping.extractfn(element, joinstr=joinstr, _=_)
                if value:
                    value = value.strip()
                if value or True:
                    yield [agencynum or '', key, record_type, unicode(mapping.FieldID), mapping.FieldName, culture, value or u'']

            # NOTE this return must happen on the end event when element is root
            return


def convert_xml(source_file, dest_file, culture, _):
    processed = set()

    xmlfile = open_zipfile(source_file)

    iterable = etree.iterparse(xmlfile, events=('start', 'end'))
    event, element = next(iterable)
    converted = _convert_part(processed, processed, iterable, element, 'Source', culture, _=_)

    header = ['AgencyNUM', 'NUM', 'Record Type', 'LookupID', 'FieldNameInDatabase', 'CultureCode', 'FieldValue']
    data = itertools.chain([header], converted)
    with open(dest_file, 'wb') as fd:
        if dest_file.endswith('.zip'):
            with bufferedzip.BufferedZipFile(fd, 'w', zipfile.ZIP_DEFLATED) as zip:
                _write_csv_to_zip(zip, data, os.path.basename(dest_file)[:-4] + '.csv')
        else:
            _write_csv(fd, data)


def _write_csv(csvfile, data, **kwargs):
    # required to have all spreadsheet programs
    # understand Unicode
    csvfile.write(codecs.BOM_UTF8)

    csvwriter = UTF8CSVWriter(csvfile, **kwargs)

    csvwriter.writerows(data)


def _write_csv_to_zip(zip, data, fname, **kwargs):
    csvfile = tempfile.TemporaryFile()

    _write_csv(csvfile, data, **kwargs)

    csvfile.seek(0)
    zip.writebuffer(csvfile, fname)
    csvfile.close()


def physical_location_description(root_element, joinstr=u'; ', _=None):
    if not _:
        _ = lambda x: x

    cross_street_label = _(u'Cross Street: ')

    parts = []
    part = root_element.xpath('CrossStreet/text()')
    if part:
        parts.append(cross_street_label + part[0])

    part = root_element.xpath('PhysicalLocationDescription/text()')
    if part:
        parts.append(part[0])

    return joinstr.join(parts)


def languages_offered(root_element, joinstr=u'; ', _=None):
    if not _:
        _ = lambda x: x

    dash_sep = _(u' - ')
    return joinstr.join(dash_sep.join(x.xpath('*/text()')) for x in root_element.xpath('Languages'))


def eligibility(root_element, joinstr=u'; ', _=None):
    if not _:
        _ = lambda x: x

    age_label = _(u'Age Requirements: ')
    residency_label = _(u'Residency Requirements: ')

    parts = []

    part = root_element.xpath('OtherRequirements/text()')
    if part:
        parts.append(part[0])

    residency = root_element.xpath('ResidencyRequirements/text()')

    part = root_element.xpath('AgeRequirements/text()')
    if part:
        parts.append(age_label + part[0] + (joinstr if residency else u''))

    part = residency
    if part:
        parts.append(residency_label + part[0])

    return u'<br /><br />'.join(parts)


def xpath_join(xpath, root_element, joinstr=u'; ', _=None):
    return joinstr.join(root_element.xpath(xpath)) or None

airs_type_mapping = {
    u'Source': [],
    u'Agency': [
        FieldMapping(1, u'AgencyNamePublic', partial(xpath_join, 'Name/text()')),
        FieldMapping(4, u'AgencyNameAlternate', partial(xpath_join, 'AKA/Name/text()')),
        FieldMapping(5, u'AgencyDescription', partial(xpath_join, 'AgencyDescription/text()')),

        FieldMapping(46, u'PhoneTollFree', partial(xpath_join, 'Phone[@TollFree = "true" and ./Type/text() = "Voice" and ./Description/text() = "Toll Free"]/PhoneNumber/text()')),
        FieldMapping(47, u'PhoneNumberHotline', partial(xpath_join, 'Phone[./Type/text() = "Voice" and ./Description/text() = "Crisis"]/PhoneNumber/text()')),
        FieldMapping(49, u'PhoneNumberAfterHours', partial(xpath_join, 'Phone[./Type/text() = "Voice" and ./Description/text() = "After Hours"]/PhoneNumber/text()')),
        FieldMapping(50, u'PhoneNumberBusinessLine', partial(xpath_join, 'Phone[./Type/text() = "Voice" and ./Description/text() = "Office"]/PhoneNumber/text()')),
        FieldMapping(51, u'PhoneFax', partial(xpath_join, 'Phone[./Type/text() = "Fax"]/PhoneNumber/text()')),
        FieldMapping(52, u'PhoneTTY', partial(xpath_join, 'Phone[./Type/text() = "TTY/TDD"]/PhoneNumber/text()')),

        FieldMapping(59, u'WebsiteAddress', partial(xpath_join, 'URL/Address/text()')),
        FieldMapping(58, u'EmailAddressMain', partial(xpath_join, 'Email/Address/text()')),

        FieldMapping(83, u'IRSStatus', partial(xpath_join, 'IRSStatus/text()')),
        FieldMapping(84, u'LegalStatus', partial(xpath_join, '@LegalStatus')),
        FieldMapping(79, u'SourceOfFunds', partial(xpath_join, 'SourceOfFunds/text()')),

        FieldMapping(68, u'LastVerifiedOn', partial(xpath_join, 'ResourceInfo/@DateLastVerified')),
        FieldMapping(69, u'LastVerifiedByName', partial(xpath_join, 'ResourceInfo/Contact/Name/text()')),
        FieldMapping(70, u'LastVerifiedByTitle', partial(xpath_join, 'ResourceInfo/Contact/Title/text()')),
        FieldMapping(71, u'LastVerifiedByEmailAddress', partial(xpath_join, 'ResourceInfo/Contact/Email/Address/text()')),
        FieldMapping(72, u'LastVerifiedByPhoneNumber', partial(xpath_join, 'ResourceInfo/Contact/Phone[Type/text() = "Voice"]/PhoneNumber/text()')),

        FieldMapping(61, u'MainContactTitle', partial(xpath_join, 'Contact[@Type = "Primary Executive"]/Title/text()')),
        FieldMapping(60, u'MainContactName', partial(xpath_join, 'Contact[@Type = "Primary Executive"]/Name/text()')),
        FieldMapping(62, u'MainContactPhoneNumber', partial(xpath_join, 'Contact[@Type = "Primary Executive"]/Phone/PhoneNumber/text()')),
        FieldMapping(63, u'MainContactEmailAddress', partial(xpath_join, 'Contact[@Type = "Primary Executive"]/Email/Address/text()')),

        FieldMapping(25, u'PhysicalAddress1', partial(xpath_join, 'AgencyLocation/PhysicalAddress/*[self::PreAddressLine or self::Line1]/text()')),
        FieldMapping(26, u'PhysicalAddress2', partial(xpath_join, 'AgencyLocation/PhysicalAddress/Line2/text()')),
        FieldMapping(28, u'PhysicalCity', partial(xpath_join, 'AgencyLocation/PhysicalAddress/City/text()')),
        FieldMapping(30, u'PhysicalStateProvince', partial(xpath_join, 'AgencyLocation/PhysicalAddress/State/text()')),
        FieldMapping(31, u'PhysicalCountry', partial(xpath_join, 'AgencyLocation/PhysicalAddress/Country/text()')),
        FieldMapping(32, u'PhysicalPostalCode', partial(xpath_join, 'AgencyLocation/PhysicalAddress/ZipCode/text()')),

        FieldMapping(39, u'MailingAddress1', partial(xpath_join, 'AgencyLocation/MailingAddress/*[self::PreAddressLine or self::Line1]/text()')),
        FieldMapping(40, u'MailingAddress2', partial(xpath_join, 'AgencyLocation/MailingAddress/Line2/text()')),
        FieldMapping(41, u'MailingCity', partial(xpath_join, 'AgencyLocation/MailingAddress/City/text()')),
        FieldMapping(43, u'MailingPostalCode', partial(xpath_join, 'AgencyLocation/MailingAddress/ZipCode/text()')),
        FieldMapping(44, u'MailingCountry', partial(xpath_join, 'AgencyLocation/MailingAddress/Country/text()')),
        FieldMapping(45, u'MailingStateProvince', partial(xpath_join, 'AgencyLocation/MailingAddress/State/text()')),
    ],
    u'Site': [
        FieldMapping(1, u'AgencyNamePublic', partial(xpath_join, 'Name/text()')),
        FieldMapping(4, u'AgencyNameAlternate', partial(xpath_join, 'AKA/Name/text()')),
        FieldMapping(25, u'PhysicalAddress1', partial(xpath_join, 'PhysicalAddress/*[self::PreAddressLine or self::Line1]/text()')),
        FieldMapping(26, u'PhysicalAddress2', partial(xpath_join, 'PhysicalAddress/Line2/text()')),
        FieldMapping(28, u'PhysicalCity', partial(xpath_join, 'PhysicalAddress/City/text()')),
        FieldMapping(30, u'PhysicalStateProvince', partial(xpath_join, 'PhysicalAddress/State/text()')),
        FieldMapping(31, u'PhysicalCountry', partial(xpath_join, 'PhysicalAddress/Country/text()')),
        FieldMapping(32, u'PhysicalPostalCode', partial(xpath_join, 'PhysicalAddress/ZipCode/text()')),

        FieldMapping(39, u'MailingAddress1', partial(xpath_join, 'MailingAddress/*[self::PreAddressLine or self::Line1]/text()')),
        FieldMapping(40, u'MailingAddress2', partial(xpath_join, 'MailingAddress/Line2/text()')),
        FieldMapping(41, u'MailingCity', partial(xpath_join, 'MailingAddress/City/text()')),
        FieldMapping(43, u'MailingPostalCode', partial(xpath_join, 'MailingAddress/ZipCode/text()')),
        FieldMapping(44, u'MailingCountry', partial(xpath_join, 'MailingAddress/Country/text()')),
        FieldMapping(45, u'MailingStateProvince', partial(xpath_join, 'MailingAddress/State/text()')),


        FieldMapping(46, u'PhoneTollFree', partial(xpath_join, 'Phone[@TollFree = "true" and ./Type/text() = "Voice" and ./Description/text() = "Toll Free"]/PhoneNumber/text()')),
        FieldMapping(47, u'PhoneNumberHotline', partial(xpath_join, 'Phone[./Type/text() = "Voice" and ./Description/text() = "Crisis"]/PhoneNumber/text()')),
        FieldMapping(49, u'PhoneNumberAfterHours', partial(xpath_join, 'Phone[./Type/text() = "Voice" and ./Description/text() = "After Hours"]/PhoneNumber/text()')),
        FieldMapping(50, u'PhoneNumberBusinessLine', partial(xpath_join, 'Phone[./Type/text() = "Voice" and ./Description/text() = "Office"]/PhoneNumber/text()')),
        FieldMapping(51, u'PhoneFax', partial(xpath_join, 'Phone[./Type/text() = "Fax"]/PhoneNumber/text()')),
        FieldMapping(52, u'PhoneTTY', partial(xpath_join, 'Phone[./Type/text() = "TTY/TDD"]/PhoneNumber/text()')),

        FieldMapping(59, u'WebsiteAddress', partial(xpath_join, 'URL/Address/text()')),
        FieldMapping(58, u'EmailAddressMain', partial(xpath_join, 'Email/Address/text()')),

        FieldMapping(61, u'MainContactTitle', partial(xpath_join, 'Contact[@Type = "Primary Contact"]/Title/text()')),
        FieldMapping(60, u'MainContactName', partial(xpath_join, 'Contact[@Type = "Primary Contact"]/Name/text()')),
        FieldMapping(62, u'MainContactPhoneNumber', partial(xpath_join, 'Contact[@Type = "Primary Contact"]/Phone/PhoneNumber/text()')),
        FieldMapping(63, u'MainContactEmailAddress', partial(xpath_join, 'Contact[@Type = "Primary Contact"]/Email/Address/text()')),

        FieldMapping(36, u'DisabilitiesAccess', partial(xpath_join, 'DisabilitiesAccess/text()')),
        FieldMapping(34, u'HoursOfOperation', partial(xpath_join, 'TimeOpen/Notes/text()')),

        FieldMapping(5, u'AgencyDescription', partial(xpath_join, 'SiteDescription/text()')),
        FieldMapping(35, u'PhysicalLocationDescription', physical_location_description),

        FieldMapping(13, u'LanguagesOffered', languages_offered),
    ],
    u'SiteService': [
        FieldMapping(1, u'AgencyNamePublic', partial(xpath_join, 'Name/text()')),
        FieldMapping(4, u'AgencyNameAlternate', partial(xpath_join, 'AKA/Name/text()')),

        FieldMapping(46, u'PhoneTollFree', partial(xpath_join, 'Phone[@TollFree = "true" and ./Type/text() = "Voice" and ./Description/text() = "Toll Free"]/PhoneNumber/text()')),
        FieldMapping(47, u'PhoneNumberHotline', partial(xpath_join, 'Phone[./Type/text() = "Voice" and ./Description/text() = "Crisis"]/PhoneNumber/text()')),
        FieldMapping(49, u'PhoneNumberAfterHours', partial(xpath_join, 'Phone[./Type/text() = "Voice" and ./Description/text() = "After Hours"]/PhoneNumber/text()')),
        FieldMapping(50, u'PhoneNumberBusinessLine', partial(xpath_join, 'Phone[./Type/text() = "Voice" and ./Description/text() = "Office"]/PhoneNumber/text()')),
        FieldMapping(51, u'PhoneFax', partial(xpath_join, 'Phone[./Type/text() = "Fax"]/PhoneNumber/text()')),
        FieldMapping(52, u'PhoneTTY', partial(xpath_join, 'Phone[./Type/text() = "TTY/TDD"]/PhoneNumber/text()')),

        FieldMapping(59, u'WebsiteAddress', partial(xpath_join, 'URL/Address/text()')),
        FieldMapping(58, u'EmailAddressMain', partial(xpath_join, 'Email/Address/text()')),

        FieldMapping(24, u'CoverageArea', partial(xpath_join, 'GeographicAreaServed/Description/text()')),

        FieldMapping(61, u'MainContactTitle', partial(xpath_join, 'Contact[@Type = "Primary Contact"]/Title/text()')),
        FieldMapping(60, u'MainContactName', partial(xpath_join, 'Contact[@Type = "Primary Contact"]/Name/text()')),
        FieldMapping(62, u'MainContactPhoneNumber', partial(xpath_join, 'Contact[@Type = "Primary Contact"]/Phone/PhoneNumber/text()')),
        FieldMapping(63, u'MainContactEmailAddress', partial(xpath_join, 'Contact[@Type = "Primary Contact"]/Email/Address/text()')),

        FieldMapping(68, u'LastVerifiedOn', partial(xpath_join, 'ResourceInfo/@DateLastVerified')),
        FieldMapping(69, u'LastVerifiedByName', partial(xpath_join, 'ResourceInfo/Contact/Name/text()')),
        FieldMapping(70, u'LastVerifiedByTitle', partial(xpath_join, 'ResourceInfo/Contact/Title/text()')),
        FieldMapping(71, u'LastVerifiedByEmailAddress', partial(xpath_join, 'ResourceInfo/Contact/Email/Address/text()')),
        FieldMapping(72, u'LastVerifiedByPhoneNumber', partial(xpath_join, 'ResourceInfo/Contact/Phone[Type/text() = "Voice"]/PhoneNumber/text()')),

        FieldMapping(14, u'FeeStructureSource', partial(xpath_join, 'FeeStructure/text()')),
        FieldMapping(15, u'ApplicationProcess', partial(xpath_join, 'ApplicationProcess/Description/text()')),
        FieldMapping(13, u'LanguagesOffered', languages_offered),
        FieldMapping(81, u'InternalNotesForEditorsAndViewers', partial(xpath_join, 'InternalNote/text()')),
        FieldMapping(11, u'Eligibility', eligibility),

    ]


}

_tag_to_type_map = {
    'Agency': 'AGENCY', 'Site': 'SITE', 'SiteService': 'PROGRAM'
}
