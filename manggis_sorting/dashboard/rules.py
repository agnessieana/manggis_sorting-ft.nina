# rules.py
# Basis Pengetahuan dari Jurnal Farha Fitrahul Janah (2021)

GEJALA = {
    "G01": "Kulit buah tampak kehitaman dan mengkilat",
    "G02": "Kulit buah berubah warna",
    "G03": "Buah matang membusuk setelah dipetik",
    "G04": "Pangkal buah dan tangkai menghitam",
    "G05": "Warna hitam meluas ke seluruh buah",

    "G06": "Kulit batang atau cabang kering",
    "G07": "Daun menjadi pucat",
    "G08": "Batang mengeluarkan getah",
    "G09": "Warna batang berubah",
    "G10": "Bunga tidak normal",
    "G11": "Buah tidak normal",
    "G12": "Daun kering dan rontok",
    "G13": "Getah menggumpal di bawah kulit",

    "G14": "Jamur pada akar",
    "G15": "Titik hitam pada kayu akar",
    "G16": "Daun menguning dan layu",

    "G17": "Jamur seperti benang perak",
    "G18": "Jamur menjadi kerak merah",
    "G19": "Cabang tanaman mati",

    "G20": "Bercak tidak beraturan pada daun",
    "G21": "Bercak kelabu atau coklat",
    "G22": "Ujung daun mengering",
    "G23": "Bercak menjalar",
    "G24": "Daun menggulung",
    "G25": "Hitam di sisi daun"
}

RULES = {
    "P01 Busuk Buah": ["G01", "G02", "G03", "G04", "G05"],
    "P02 Kanker Batang": ["G06", "G07", "G08", "G09", "G10", "G11", "G12", "G13"],
    "P03 Busuk Akar": ["G14", "G15", "G16", "G12"],
    "P04 Jamur Upas": ["G17", "G18", "G19"],
    "P05 Bercak Daun": ["G12", "G20", "G21", "G22", "G23", "G24", "G25"]
}
