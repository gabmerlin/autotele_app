"""
Utilitaire pour mapper les numéros de téléphone vers les drapeaux de pays.
Basé sur les préfixes internationaux téléphoniques.
"""
from typing import Optional
import re


# Mapping des préfixes téléphoniques vers codes pays (ISO 3166-1 alpha-2)
# Trié par longueur décroissante pour matcher les préfixes les plus longs en premier
PHONE_PREFIX_TO_COUNTRY = {
    # Préfixes à 4 chiffres
    '1242': 'BS',  # Bahamas
    '1246': 'BB',  # Barbados
    '1264': 'AI',  # Anguilla
    '1268': 'AG',  # Antigua and Barbuda
    '1284': 'VG',  # British Virgin Islands
    '1340': 'VI',  # US Virgin Islands
    '1345': 'KY',  # Cayman Islands
    '1441': 'BM',  # Bermuda
    '1473': 'GD',  # Grenada
    '1649': 'TC',  # Turks and Caicos
    '1664': 'MS',  # Montserrat
    '1670': 'MP',  # Northern Mariana Islands
    '1671': 'GU',  # Guam
    '1684': 'AS',  # American Samoa
    '1721': 'SX',  # Sint Maarten
    '1758': 'LC',  # Saint Lucia
    '1767': 'DM',  # Dominica
    '1784': 'VC',  # Saint Vincent and Grenadines
    '1787': 'PR',  # Puerto Rico
    '1809': 'DO',  # Dominican Republic
    '1829': 'DO',  # Dominican Republic
    '1849': 'DO',  # Dominican Republic
    '1868': 'TT',  # Trinidad and Tobago
    '1869': 'KN',  # Saint Kitts and Nevis
    '1876': 'JM',  # Jamaica
    
    # Préfixes à 3 chiffres
    '247': 'AC',  # Ascension Island
    '290': 'SH',  # Saint Helena
    '297': 'AW',  # Aruba
    '298': 'FO',  # Faroe Islands
    '299': 'GL',  # Greenland
    '350': 'GI',  # Gibraltar
    '351': 'PT',  # Portugal
    '352': 'LU',  # Luxembourg
    '353': 'IE',  # Ireland
    '354': 'IS',  # Iceland
    '355': 'AL',  # Albania
    '356': 'MT',  # Malta
    '357': 'CY',  # Cyprus
    '358': 'FI',  # Finland
    '359': 'BG',  # Bulgaria
    '370': 'LT',  # Lithuania
    '371': 'LV',  # Latvia
    '372': 'EE',  # Estonia
    '373': 'MD',  # Moldova
    '374': 'AM',  # Armenia
    '375': 'BY',  # Belarus
    '376': 'AD',  # Andorra
    '377': 'MC',  # Monaco
    '378': 'SM',  # San Marino
    '380': 'UA',  # Ukraine
    '381': 'RS',  # Serbia
    '382': 'ME',  # Montenegro
    '383': 'XK',  # Kosovo
    '385': 'HR',  # Croatia
    '386': 'SI',  # Slovenia
    '387': 'BA',  # Bosnia and Herzegovina
    '389': 'MK',  # North Macedonia
    '420': 'CZ',  # Czech Republic
    '421': 'SK',  # Slovakia
    '423': 'LI',  # Liechtenstein
    '500': 'FK',  # Falkland Islands
    '501': 'BZ',  # Belize
    '502': 'GT',  # Guatemala
    '503': 'SV',  # El Salvador
    '504': 'HN',  # Honduras
    '505': 'NI',  # Nicaragua
    '506': 'CR',  # Costa Rica
    '507': 'PA',  # Panama
    '508': 'PM',  # Saint Pierre and Miquelon
    '509': 'HT',  # Haiti
    '590': 'GP',  # Guadeloupe
    '591': 'BO',  # Bolivia
    '592': 'GY',  # Guyana
    '593': 'EC',  # Ecuador
    '594': 'GF',  # French Guiana
    '595': 'PY',  # Paraguay
    '596': 'MQ',  # Martinique
    '597': 'SR',  # Suriname
    '598': 'UY',  # Uruguay
    '599': 'CW',  # Curaçao
    '670': 'TL',  # East Timor
    '672': 'NF',  # Norfolk Island
    '673': 'BN',  # Brunei
    '674': 'NR',  # Nauru
    '675': 'PG',  # Papua New Guinea
    '676': 'TO',  # Tonga
    '677': 'SB',  # Solomon Islands
    '678': 'VU',  # Vanuatu
    '679': 'FJ',  # Fiji
    '680': 'PW',  # Palau
    '681': 'WF',  # Wallis and Futuna
    '682': 'CK',  # Cook Islands
    '683': 'NU',  # Niue
    '685': 'WS',  # Samoa
    '686': 'KI',  # Kiribati
    '687': 'NC',  # New Caledonia
    '688': 'TV',  # Tuvalu
    '689': 'PF',  # French Polynesia
    '690': 'TK',  # Tokelau
    '691': 'FM',  # Micronesia
    '692': 'MH',  # Marshall Islands
    '850': 'KP',  # North Korea
    '852': 'HK',  # Hong Kong
    '853': 'MO',  # Macau
    '855': 'KH',  # Cambodia
    '856': 'LA',  # Laos
    '880': 'BD',  # Bangladesh
    '886': 'TW',  # Taiwan
    '960': 'MV',  # Maldives
    '961': 'LB',  # Lebanon
    '962': 'JO',  # Jordan
    '963': 'SY',  # Syria
    '964': 'IQ',  # Iraq
    '965': 'KW',  # Kuwait
    '966': 'SA',  # Saudi Arabia
    '967': 'YE',  # Yemen
    '968': 'OM',  # Oman
    '970': 'PS',  # Palestine
    '971': 'AE',  # United Arab Emirates
    '972': 'IL',  # Israel
    '973': 'BH',  # Bahrain
    '974': 'QA',  # Qatar
    '975': 'BT',  # Bhutan
    '976': 'MN',  # Mongolia
    '977': 'NP',  # Nepal
    '992': 'TJ',  # Tajikistan
    '993': 'TM',  # Turkmenistan
    '994': 'AZ',  # Azerbaijan
    '995': 'GE',  # Georgia
    '996': 'KG',  # Kyrgyzstan
    '998': 'UZ',  # Uzbekistan
    
    # Préfixes à 2 chiffres
    '20': 'EG',   # Egypt
    '27': 'ZA',   # South Africa
    '30': 'GR',   # Greece
    '31': 'NL',   # Netherlands
    '32': 'BE',   # Belgium
    '33': 'FR',   # France
    '34': 'ES',   # Spain
    '36': 'HU',   # Hungary
    '39': 'IT',   # Italy
    '40': 'RO',   # Romania
    '41': 'CH',   # Switzerland
    '43': 'AT',   # Austria
    '44': 'GB',   # United Kingdom
    '45': 'DK',   # Denmark
    '46': 'SE',   # Sweden
    '47': 'NO',   # Norway
    '48': 'PL',   # Poland
    '49': 'DE',   # Germany
    '51': 'PE',   # Peru
    '52': 'MX',   # Mexico
    '53': 'CU',   # Cuba
    '54': 'AR',   # Argentina
    '55': 'BR',   # Brazil
    '56': 'CL',   # Chile
    '57': 'CO',   # Colombia
    '58': 'VE',   # Venezuela
    '60': 'MY',   # Malaysia
    '61': 'AU',   # Australia
    '62': 'ID',   # Indonesia
    '63': 'PH',   # Philippines
    '64': 'NZ',   # New Zealand
    '65': 'SG',   # Singapore
    '66': 'TH',   # Thailand
    '81': 'JP',   # Japan
    '82': 'KR',   # South Korea
    '84': 'VN',   # Vietnam
    '86': 'CN',   # China
    '90': 'TR',   # Turkey
    '91': 'IN',   # India
    '92': 'PK',   # Pakistan
    '93': 'AF',   # Afghanistan
    '94': 'LK',   # Sri Lanka
    '95': 'MM',   # Myanmar
    '98': 'IR',   # Iran
    
    # Préfixes à 1 chiffre (USA, Canada, Russie)
    '1': 'US',    # USA/Canada (par défaut USA)
    '7': 'RU',    # Russia/Kazakhstan
}

# Mapping code pays → emoji drapeau
# Unicode Regional Indicator Symbols (U+1F1E6 à U+1F1FF)
def country_code_to_flag(country_code: str) -> str:
    """
    Convertit un code pays ISO en emoji drapeau.
    
    Args:
        country_code: Code pays ISO 3166-1 alpha-2 (ex: 'FR', 'US')
        
    Returns:
        str: Emoji drapeau
        
    Examples:
        >>> country_code_to_flag('FR')
        '🇫🇷'
        >>> country_code_to_flag('US')
        '🇺🇸'
    """
    if not country_code or len(country_code) != 2:
        return ''
    
    # Convertir les lettres en Regional Indicator Symbols
    # A = U+1F1E6, B = U+1F1E7, ..., Z = U+1F1FF
    country_code = country_code.upper()
    flag = ''.join(chr(0x1F1E6 + ord(char) - ord('A')) for char in country_code)
    return flag


def get_country_code_from_phone(phone: str) -> Optional[str]:
    """
    Extrait le code pays d'un numéro de téléphone.
    
    Args:
        phone: Numéro de téléphone (avec ou sans +)
        
    Returns:
        Optional[str]: Code pays ISO ou None
        
    Examples:
        >>> get_country_code_from_phone('+33612345678')
        'FR'
        >>> get_country_code_from_phone('79123456789')
        'RU'
        >>> get_country_code_from_phone('+1234567890')
        'US'
    """
    if not phone:
        return None
    
    # Nettoyer le numéro (garder seulement les chiffres)
    clean_phone = re.sub(r'[^\d]', '', phone)
    
    if not clean_phone:
        return None
    
    # Essayer de matcher les préfixes (du plus long au plus court)
    # Trier les préfixes par longueur décroissante
    sorted_prefixes = sorted(PHONE_PREFIX_TO_COUNTRY.keys(), key=len, reverse=True)
    
    for prefix in sorted_prefixes:
        if clean_phone.startswith(prefix):
            return PHONE_PREFIX_TO_COUNTRY[prefix]
    
    return None


def get_country_flag_from_phone(phone: str) -> Optional[str]:
    """
    Récupère l'emoji drapeau d'un pays à partir d'un numéro de téléphone.
    
    Args:
        phone: Numéro de téléphone (avec ou sans +)
        
    Returns:
        Optional[str]: Emoji drapeau ou None
        
    Examples:
        >>> get_country_flag_from_phone('+33612345678')
        '🇫🇷'
        >>> get_country_flag_from_phone('79123456789')
        '🇷🇺'
        >>> get_country_flag_from_phone('+1234567890')
        '🇺🇸'
    """
    country_code = get_country_code_from_phone(phone)
    if country_code:
        return country_code_to_flag(country_code)
    return None


def get_country_name(country_code: str) -> Optional[str]:
    """
    Récupère le nom du pays à partir du code ISO.
    
    Args:
        country_code: Code pays ISO 3166-1 alpha-2
        
    Returns:
        Optional[str]: Nom du pays ou None
    """
    # Mapping simplifié des codes vers noms (principaux pays)
    country_names = {
        'FR': 'France',
        'US': 'États-Unis',
        'GB': 'Royaume-Uni',
        'DE': 'Allemagne',
        'ES': 'Espagne',
        'IT': 'Italie',
        'RU': 'Russie',
        'CN': 'Chine',
        'JP': 'Japon',
        'KR': 'Corée du Sud',
        'IN': 'Inde',
        'BR': 'Brésil',
        'CA': 'Canada',
        'AU': 'Australie',
        'MX': 'Mexique',
        'AR': 'Argentine',
        'NL': 'Pays-Bas',
        'BE': 'Belgique',
        'CH': 'Suisse',
        'SE': 'Suède',
        'NO': 'Norvège',
        'DK': 'Danemark',
        'FI': 'Finlande',
        'PL': 'Pologne',
        'UA': 'Ukraine',
        'TR': 'Turquie',
        'SA': 'Arabie Saoudite',
        'AE': 'Émirats Arabes Unis',
        'EG': 'Égypte',
        'ZA': 'Afrique du Sud',
        'NG': 'Nigeria',
        'TH': 'Thaïlande',
        'VN': 'Vietnam',
        'ID': 'Indonésie',
        'MY': 'Malaisie',
        'SG': 'Singapour',
        'PH': 'Philippines',
        'NZ': 'Nouvelle-Zélande',
        'PT': 'Portugal',
        'GR': 'Grèce',
        'CZ': 'République Tchèque',
        'HU': 'Hongrie',
        'RO': 'Roumanie',
        'AT': 'Autriche',
        'IL': 'Israël',
        'IR': 'Iran',
        'IQ': 'Irak',
        'PK': 'Pakistan',
        'BD': 'Bangladesh',
    }
    
    return country_names.get(country_code.upper()) if country_code else None

