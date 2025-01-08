
########## GLOBALS #############################################################


# Maximum characteres in description
MAX_DESC_LEN = 250

# Some functions need a page key to add to the variables
# they create in session state. The keys refer to the pages:
# Filter Search:    filtersearch
# My Lessons:       mylessons
# Manage Lessons:   admin
PAGE_KEYS = [
    'filtersearch',
    'mylessons',
    'admin'
]

# Fields that we want to show as tags in lesson overview
TAG_FIELDS = [
    'AdC',
    'Destination_Country',
    'Segment', 
    'Scope', 
]

# Icon associated to each status
STATUS_ICON = {
    'Approved': '🟢', 
    'Pending': '🟡', 
    'Rejected': '🔴',
    'Draft': '🔵'
}

# Color associated to each status
STATUS_COLOR = {
    'Approved': 'green',
    'Pending': 'orange',
    'Rejected': 'red',
    'Draft': 'blue'
}


######### SELECTBOXES ##########################################################

# The options that appear in each selectbox

STATUS_OPTIONS = [
    'Approved', 
    'Pending', 
    'Rejected',
    'Draft'
]

OPTIONS_TECH = [
    'MCSET',
    'PIX',
    'FLUSARC',
    'RM6/RM AIRSET',
    'SM6/SM AIRSET',
    'PREMSET',
    'F400',
    'WI',
    'GHA',
    'CBGS',
    'GBCD',
    'UPS GVX',
    'UPS GVS/GVL',
    'Chillers',
    'CRAHS',
    'OKKEN',
    'Drivers',
    'PME',
    'EPO',
    'Aveva PI'
]

OPTIONS_SCOPE = [
    'Supply',
    'FAT',
    'Transport',
    'SAT',
    'PEM supervision',
    'Assembly/Installation',
    'Comissioning'
]

OPTIONS_SEGMENT = [
    'CPG',
    'MMM',
    'WWW',
    'Energies and Chemicals'
    'OEM',
    'Enterprise IT',
    'Office and Publics Buildings',
    'Healthcare',
    'Hotels',
    'Residential',
    'Grid',
    'Transportation',
    'Cloud and Service Providers']

OPTIONS_COUNTRY = [
    'Spain',
    'France'
]

OPTIONS_ADC = [
    'Design and Technical Scope',
    'Contract',
    'Management',
    'Supply Chain',
    'Health & Security',
    'Quality'
    'Services'
]

OPTIONS_IG = [
    'Qatar Services',
    'China Factory'
]
