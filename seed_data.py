import sqlite3
import json
from database import get_db, init_db

def seed_database():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    # Clear existing data to allow clean re-runs
    cursor.execute("DELETE FROM categories")
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM serviceable_pincodes")
    cursor.execute("DELETE FROM reviews")

    categories = [
        (
            "pedha",
            "Signature Pedhas",
            "खास कंदी पेढे",
            "Our legendary slow-cooked caramelized mawa pedhas handcrafted in Satara.",
            "/static/images/official/satari-kandi-pedhe.jpg",
            1
        ),
        (
            "barfi",
            "Royal Barfis",
            "शाही बर्फी व मिठाई",
            "Exquisite mawa confections crafted with pistachios, gulkand, anjir, mango and fresh cream.",
            "/static/images/official/pista-barfi.jpg",
            2
        ),
        (
            "traditional-mithai",
            "Classic Sweets & Laddus",
            "पारंपारिक मिठाई व लाडू",
            "Pure desi ghee Kajukadli, Maisurpak, Dink Ladu, and festive assorted mithai boxes.",
            "/static/images/official/kajukadli.jpg",
            3
        ),
        (
            "namkeen-farsan",
            "Authentic Namkeen & Farsan",
            "पारंपारिक फरसाण व भडंग",
            "Crispy Mahalaxmi Farsana, Sai Lasun Farsana, Misal Farsana, and spicy Kolhapuri Bhadang.",
            "/static/images/official/special-mahalaxmi-farsana-9.jpg",
            4
        ),
        (
            "bakery-cookies",
            "Bakery, Khari & Cookies",
            "बेकरी, खारी व कुकीज",
            "Crispy Palekar Khari, Butter, Suji Toast, Milk Pedha Cookies, and fresh Mawa Cake.",
            "/static/images/official/palekar-butter-36.jpg",
            5
        ),
        (
            "syrups-squash",
            "Fruit Squashes & Syrups",
            "सिरप, फालुदा व स्क्वॅश",
            "Refreshing Rose, Khus, Alphonso Mango, Lemon Pudina Squashes and Falooda Syrups.",
            "/static/images/official/special-rose-syrup-3.jpg",
            6
        ),
        (
            "organic-staples",
            "Pure Jaggery & Dry Fruits",
            "सेंद्रिय गूळ व सुकामेवा",
            "Natural Kolhapuri Jaggery Cubes & Powder, Whole Cashews, and Lemongrass Powder.",
            "/static/images/official/jaggery-cube-500gms-19.jpg",
            7
        )
    ]

    cursor.executemany("""
    INSERT INTO categories (id, name, name_mr, description, image_url, display_order)
    VALUES (?, ?, ?, ?, ?, ?)
    """, categories)

    products = [
        # --- 1. SIGNATURE PEDHAS ---
        (
            "satara-kandi-pedha",
            "pedha",
            "Satari Kandi Pedhe",
            "सातारी खास कंदी पेढे",
            "The iconic caramelized dark brown pedha slow-cooked for 8 hours",
            "Our flagship pride! Prepared using thick buffalo milk mawa, slow-roasted in heavy copper vats until deep amber caramelization, seasoned with fragrant green cardamom and sugar grains. The authentic taste of Satara.",
            "/static/images/official/satari-kandi-pedhe.jpg",
            "Mama's Signature",
            190, 360, 700,
            20,
            "Pure Buffalo Milk Khoya (Mawa), Sugar, Fresh Green Cardamom, Nutmeg",
            1, 0, 1, 0, 1, 4.9, 284
        ),
        (
            "special-jaggery-kandi-pedha",
            "pedha",
            "Special Jaggery Kandi Pedha",
            "स्पेशल गुळाचा कंदी पेढा",
            "Caramelized mawa pedha sweetened with natural Kolhapuri jaggery",
            "Traditional Satara pedha crafted with pure organic Kolhapuri gul (jaggery) instead of refined sugar. Imparts a rich earthy sweetness and deep caramel aroma.",
            "/static/images/official/special-jaggery-kandi-pedha.jpg",
            "Jaggery Special",
            200, 380, 740,
            20,
            "Pure Milk Mawa, Kolhapuri Natural Jaggery, Green Cardamom, Desi Ghee",
            1, 0, 1, 0, 1, 4.9, 195
        ),
        (
            "special-kesar-kandi-pedha",
            "pedha",
            "Special Kesar Kandi Pedha",
            "स्पेशल केशर कंदी पेढा",
            "Infused with authentic Kashmiri saffron strands and cardamom",
            "Royal mawa pedha infused with handpicked pure Kashmiri saffron (kesar), offering a rich golden amber hue and delicate royal fragrance.",
            "/static/images/official/special-kesar-kandi-pedha.jpg",
            "Bestseller",
            220, 420, 820,
            18,
            "Pure Milk Mawa, Kashmiri Kesar, Sugar, Cardamom, Pistachio slivers",
            1, 0, 1, 0, 1, 4.8, 168
        ),
        (
            "sugar-free-pedha",
            "pedha",
            "Sugar Free Pedha",
            "साखरमुक्त कंदी पेढा (शुगर फ्री)",
            "Zero added sugar for health-conscious sweet lovers",
            "Guilt-free indulgence! Prepared with slow-roasted rich mawa and natural low-glycemic plant sweeteners so everyone can relish the authentic taste of Satara.",
            "/static/images/official/sugar-free-pedha.jpg",
            "100% Sugar Free",
            210, 400, 780,
            15,
            "Pure Buffalo Milk Khoya, Natural Stevia Blend, Cardamom, Nutmeg",
            1, 1, 0, 0, 1, 4.8, 122
        ),

        # --- 2. ROYAL BARFIS ---
        (
            "pista-barfi",
            "barfi",
            "Shahi Pista Barfi",
            "शाही पिस्ता बर्फी",
            "Rich mawa confection loaded with Iranian pistachios",
            "Luxurious pistachio fudge made with premier grade khoya, blended with finely powdered roasted pistachios and topped with crunchy nut slivers.",
            "/static/images/official/pista-barfi.jpg",
            "Royal Treat",
            230, 440, 860,
            15,
            "Fresh Khoya, Iranian Pistachios, Sugar, Cardamom, Desi Ghee",
            1, 0, 1, 1, 1, 4.8, 145
        ),
        (
            "gulkand-barfi",
            "barfi",
            "Royal Gulkand Barfi",
            "शाही गुलकंद बर्फी",
            "Infused with organic rose petal preserve and rich khoya",
            "Delightful aromatic confection layered with traditional sweet rose petal gulkand, giving a cooling and refreshing floral flavor in every bite.",
            "/static/images/official/gulkand-barfi.jpg",
            "Floral Delight",
            220, 420, 820,
            15,
            "Khoya, Organic Rose Petal Gulkand, Fine Sugar, Cardamom, Desi Ghee",
            1, 0, 0, 0, 1, 4.7, 98
        ),
        (
            "malai-barfi",
            "barfi",
            "Pure Malai Barfi",
            "शुद्ध मलाई बर्फी",
            "Velvety soft and mildly sweet fresh milk fudge",
            "Crafted from freshly condensed milk cream, this velvety smooth malai barfi has a delicate sweetness that dissolves effortlessly on your palate.",
            "/static/images/official/malai-barfi.jpg",
            "Mild Sweet",
            210, 400, 780,
            12,
            "Full Cream Fresh Milk, Malai, Fine Sugar, Cardamom",
            1, 0, 0, 0, 1, 4.8, 110
        ),
        (
            "anjir-barfi",
            "barfi",
            "Turkish Anjir Dry Fruit Barfi",
            "अंजीर ड्रायफ्रूट बर्फी (नो शुगर)",
            "Naturally sweet Turkish figs blended with roasted dry fruits",
            "Zero added refined sugar! Rich Turkish figs cooked gently with chopped Californian almonds, pistachios, and cashew nuts.",
            "/static/images/official/anjir-barfi.jpg",
            "No Added Sugar",
            280, 540, 1050,
            30,
            "Turkish Dried Figs (Anjir), Roasted Cashews, Almonds, Pistachios, Pure Ghee",
            1, 1, 1, 0, 1, 4.9, 175
        ),
        (
            "butterscotch-barfi",
            "barfi",
            "Butterscotch Praline Barfi",
            "बटरस्कॉच बर्फी",
            "Crunchy butterscotch praline blended with creamy mawa",
            "Modern twist on classic mithai! Rich mawa barfi infused with crunchy caramelized butterscotch bits and creamy butter caramel aroma.",
            "/static/images/official/butterscotch-barfi.jpg",
            "Kids Favorite",
            220, 420, 820,
            18,
            "Khoya, Caramel Praline, Sugar, Desi Ghee, Butterscotch essence",
            1, 0, 0, 0, 1, 4.7, 85
        ),
        (
            "mango-barfi",
            "barfi",
            "Ratnagiri Mango Barfi",
            "रत्नागिरी हापूस आंबा बर्फी",
            "Real Alphonso mango pulp blended with rich khoya",
            "Seasonal delight made with 100% natural GI-tagged Ratnagiri Alphonso mango pulp seamlessly blended with rich khoya fudge.",
            "/static/images/official/mango-barfi.jpg",
            "Fruit Special",
            230, 440, 860,
            15,
            "Pure Milk Khoya, Alphonso Mango Pulp, Sugar, Cardamom",
            1, 0, 1, 1, 1, 4.9, 130
        ),
        (
            "strawberry-barfi",
            "barfi",
            "Mahabaleshwar Strawberry Barfi",
            "महाबळेश्वर स्ट्रॉबेरी बर्फी",
            "Fresh Mahabaleshwar strawberry crush blended with creamy mawa",
            "Celebrated local specialty combining farm-fresh Mahabaleshwar red strawberries with rich Satara khoya for a sweet and tangy gourmet sweet.",
            "/static/images/official/strawberry-barfi.jpg",
            "Regional Pride",
            220, 420, 820,
            15,
            "Pure Khoya, Strawberry Crush, Fine Sugar, Desi Ghee",
            1, 0, 0, 0, 1, 4.8, 92
        ),
        (
            "karadand-dry-fruit-barfi",
            "barfi",
            "Royal Karadand Dry Fruit Barfi",
            "शाही कारादंत ड्रायफ्रूट बर्फी",
            "Nutritious dry fruit fudge with edible gum, nuts, and jaggery",
            "Legendary energy-dense confection made with fried edible gum, dried coconut, dates, cashews, almonds, and organic jaggery in pure cow ghee.",
            "/static/images/official/karadand-dry-fruit-barfi.jpg",
            "Health & Energy",
            260, 500, 980,
            45,
            "Edible Gum, Cashews, Almonds, Pistachios, Dry Coconut, Jaggery, Pure Cow Ghee",
            1, 0, 1, 0, 1, 4.9, 105
        ),

        # --- 3. CLASSIC SWEETS & LADDUS ---
        (
            "shahi-kaju-katli",
            "traditional-mithai",
            "Shahi Kajukadli (Kaju Katli)",
            "शाही काजू कतली",
            "Diamond cut thin cashew diamonds crafted with premier Goan cashews",
            "World-class cashew confection made with zero flour or fillers. Contains 100% premier cashews ground to a velvety consistency with minimal sugar.",
            "/static/images/official/kajukadli.jpg",
            "Evergreen Star",
            260, 500, 980,
            30,
            "Premium Grade W240 Cashew Nuts, Sugar, Cardamom, Purified Water",
            0, 0, 1, 1, 1, 4.9, 360
        ),
        (
            "maisurpak",
            "traditional-mithai",
            "Shuddh Desi Ghee Maisurpak",
            "शुद्ध तुपातील म्हैसूर पाक",
            "Porous, golden melt-in-mouth traditional royal recipe",
            "Prepared with fine gram flour roasted in abundant pure cow desi ghee and dunked in aromatic syrup. Aerated honeycomb texture that melts on the tongue.",
            "/static/images/official/maisurpak.jpg",
            "Pure Ghee Classic",
            190, 360, 700,
            25,
            "Besan (Gram Flour), 100% Pure Desi Ghee, Sugar, Cardamom",
            1, 0, 0, 0, 1, 4.8, 140
        ),
        (
            "kaju-maisurpak",
            "traditional-mithai",
            "Shahi Kaju Maisurpak",
            "शाही काजू म्हैसूर पाक",
            "Luxurious blend of Goan cashew flour and golden desi ghee",
            "Gourmet adaptation of classic mysore pak made with velvety cashew nut paste and pure cow ghee. Ultra-rich and irresistible.",
            "/static/images/official/kaju-maisurpak.jpg",
            "Premium Sweet",
            250, 480, 940,
            25,
            "Pure Cashew Nut Powder, Besan, Pure Desi Ghee, Fine Sugar, Cardamom",
            1, 0, 1, 1, 1, 4.9, 115
        ),
        (
            "dink-ladu",
            "traditional-mithai",
            "Nutritious Dink Ladu (Gond Ladoo)",
            "पौष्टिक डिंकाचे लाडू (सुकामेवा)",
            "Immunity boosting winter & health laddu packed with dry fruits",
            "A nourishing powerhouse made with crisp fried edible gum (dink), dates, dry coconut, poppy seeds, cashew nuts, almonds, and dry ginger powder bound with pure ghee.",
            "/static/images/official/dink-ladu.jpg",
            "Health & Immunity",
            240, 460, 900,
            45,
            "Edible Gum (Dink), Dry Coconut, Pure Cow Ghee, Dates, Cashews, Almonds, Organic Jaggery",
            1, 0, 1, 0, 1, 4.9, 180
        ),
        (
            "mix-mithaei",
            "traditional-mithai",
            "Mama's Shahi Mix Mithaei Gift Box",
            "मामा स्पेशल मिक्स मिठाई बॉक्स",
            "Festive assortment of Satara Kandi Pedha, Barfis, and Kaju Katli",
            "The ultimate celebratory gift pack containing a rich assortment of Mama Pedhewale's signature sweets: Kandi Pedha, Kaju Katli, Pista Barfi, and Anjir Barfi.",
            "/static/images/official/mix-mithaei.jpg",
            "Gift Assortment",
            250, 480, 920,
            20,
            "Assorted Kandi Pedha, Kaju Katli, Pista Barfi, Anjir Barfi",
            1, 0, 1, 1, 1, 5.0, 290
        ),

        # --- 4. NAMKEEN & FARSAN ---
        (
            "special-mahalaxmi-farsana",
            "namkeen-farsan",
            "Special Mahalaxmi Farsana",
            "स्पेशल महालक्ष्मी फरसाण",
            "Crispy golden savory mix with spiced sev, boondi, and crunchy peanuts",
            "Authentic Satara tea-time namkeen featuring crispy spiced gram flour sev, crunchy peanuts, roasted chana dal, and mild aromatic seasoning.",
            "/static/images/official/special-mahalaxmi-farsana-9.jpg",
            "Snack Bestseller",
            110, 200, 380,
            60,
            "Gram Flour (Besan), Peanuts, Edible Vegetable Oil, Chana Dal, Spices, Salt",
            0, 0, 1, 0, 1, 4.8, 195
        ),
        (
            "sai-lasun-farsana",
            "namkeen-farsan",
            "Sai Lasun (Garlic) Farsana",
            "साई लसूण फरसाण",
            "Zesty roasted garlic flavored crispy savory mixture",
            "Infused with roasted garlic cloves, red chilli powder, and crisp sev. The bold, punchy garlic aroma makes it an addictive tea-time companion.",
            "/static/images/official/sai-lasun-farsana-16.jpg",
            "Spicy & Bold",
            115, 210, 400,
            60,
            "Besan, Fresh Roasted Garlic, Red Chilli, Peanuts, Oil, Spices, Salt",
            0, 0, 0, 0, 1, 4.8, 130
        ),
        (
            "sai-namkin-farsana",
            "namkeen-farsan",
            "Sai Namkin Farsana",
            "साई नमकीन फरसाण",
            "Mildly salted crispy golden farsan mixture",
            "Light and crunch-filled savory mixture with balanced spices, perfect for children and those who prefer mild, flavorful snacking.",
            "/static/images/official/sai-namkin-farsana-18.jpg",
            "Mild Crunch",
            110, 200, 380,
            60,
            "Gram Flour, Pure Edible Oil, Peanuts, Curry Leaves, Mild Seasoning, Salt",
            0, 0, 0, 0, 1, 4.7, 88
        ),
        (
            "shiv-ganesh-misal-farsana",
            "namkeen-farsan",
            "Shiv Ganesh Special Misal Farsana",
            "शिव गणेश खास मिसळ फरसाण",
            "Extra-crunchy thick sev mixture specially crafted for Kolhapuri/Puneri Misal",
            "Designed to stay remarkably crunchy even when drenched in piping hot spicy misal tarri! A staple for authentic Maharashtra Misal Pav lovers.",
            "/static/images/official/shiv-ganesh-misal-farsana-32.jpg",
            "Misal Special",
            115, 210, 400,
            60,
            "Coarse Besan, Spices, Red Chilli, Peanuts, Edible Oil, Salt",
            0, 0, 1, 0, 1, 4.9, 160
        ),
        (
            "gore-bandhu-bhadang",
            "namkeen-farsan",
            "Gore Bandhu Authentic Bhadang",
            "गोरे बंधू अस्सल भडंग",
            "Crisp spiced puffed rice tossed with fried garlic, peanuts, and chillies",
            "Famous regional recipe made from selected Kolhapuri puffed rice (kurmure), gently roasted with crunchy peanuts, golden garlic slivers, and chili oil.",
            "/static/images/official/gore-bandhu-bhadang-37.jpg",
            "Regional Classic",
            95, 180, 340,
            60,
            "Roasted Puffed Rice, Peanuts, Garlic, Green Chillies, Turmeric, Oil, Salt",
            0, 0, 1, 0, 1, 4.9, 210
        ),
        (
            "kolhapuri-bhadang",
            "namkeen-farsan",
            "Spicy Kolhapuri Bhadang",
            "कोल्हापुरी तिखट भडंग",
            "Fiery and crunchy spicy puffed rice snack",
            "For lovers of true Maharashtra heat! Packed with fragrant Kolhapuri masala, crisp curry leaves, and crunchy roasted groundnuts.",
            "/static/images/official/kolhapuri-bhadang-55.jpg",
            "Spicy Hot",
            95, 180, 340,
            60,
            "Puffed Rice, Kolhapuri Red Masala, Peanuts, Garlic, Curry Leaves, Oil",
            0, 0, 0, 0, 1, 4.8, 142
        ),

        # --- 5. BAKERY, KHARI & COOKIES ---
        (
            "palekar-butter",
            "bakery-cookies",
            "Palekar Special Butter Biscuits",
            "पालेकर स्पेशल बटर",
            "Traditional crisp, melt-in-mouth chai dip butter biscuits",
            "Legendary round butter biscuits baked to golden perfection. The quintessential morning tea accompaniment across Satara and Pune.",
            "/static/images/official/palekar-butter-36.jpg",
            "Tea Companion",
            85, 160, 300,
            90,
            "Refined Wheat Flour, Pure Bakery Shortening, Butter, Salt, Sugar",
            0, 0, 1, 0, 1, 4.9, 230
        ),
        (
            "palekar-crispy-khari",
            "bakery-cookies",
            "Palekar Crispy Khari",
            "पालेकर क्रिस्पी खारी",
            "Multi-layered flaky, light, and airy puff pastry biscuits",
            "Feather-light golden puff pastry biscuits baked to crisp perfection. Zero oiliness, pure flaky crunch in every single layer.",
            "/static/images/official/palekar-crispy-khari-53.jpg",
            "Crispy Puffs",
            90, 170, 320,
            90,
            "Wheat Flour, Vegetable Fat, Salt, Cold Water",
            0, 0, 1, 0, 1, 4.8, 175
        ),
        (
            "palekar-knot-khari",
            "bakery-cookies",
            "Palekar Twisted Knot Khari",
            "पालेकर नॉट खारी",
            "Artisan tied-knot crispy butter puff pastries",
            "Hand-twisted into playful knot shapes before baking, creating extra crunchy edges and an irresistible flaky texture.",
            "/static/images/official/palekar-knot-khari-35.jpg",
            "Artisan Bake",
            95, 180, 340,
            90,
            "Refined Flour, Butter Shortening, Iodized Salt",
            0, 0, 0, 0, 1, 4.7, 95
        ),
        (
            "palekar-khari-butter-jeera",
            "bakery-cookies",
            "Palekar Jeera Khari-Butter",
            "पालेकर जिरा खारी बटर",
            "Flaky butter puffs infused with roasted cumin seeds",
            "Aromatic roasted cumin (jeera) blended into buttery puff pastry layers. Delivers a subtle savory aroma that pairs heavenly with ginger chai.",
            "/static/images/official/palekar-khari-butter-jeera-23.jpg",
            "Jeera Flavor",
            95, 180, 340,
            90,
            "Wheat Flour, Roasted Jeera (Cumin), Butter, Vegetable Fat, Salt",
            0, 0, 0, 0, 1, 4.8, 115
        ),
        (
            "palekar-ajwain-toast",
            "bakery-cookies",
            "Palekar Ajwain Rusk Toast",
            "पालेकर ओवा टोस्ट",
            "Twice-baked crunchy rusks infused with carom seeds (ajwain)",
            "Digestive and flavorful twice-baked rusks with digestive ajwain seeds. Extra-crispy and satisfyingly crunchy for your breakfast tea.",
            "/static/images/official/palekar-ajwain-toast-39.jpg",
            "Digestive",
            85, 160, 300,
            90,
            "Wheat Flour, Ajwain (Carom Seeds), Yeast, Sugar, Pure Salt",
            0, 0, 0, 0, 1, 4.7, 102
        ),
        (
            "milk-pedha-cookies",
            "bakery-cookies",
            "Satara Milk Pedha Cookies",
            "मिल्क पेढा कुकीज",
            "Unique gourmet cookies crafted with authentic roasted mawa pedha",
            "A Mama Pedhewale exclusive invention! Real caramelized Satara pedha blended directly into cookie dough, producing a melt-in-mouth cardamom mawa cookie.",
            "/static/images/official/milk-pedha-cookies-43.jpg",
            "Mama's Exclusive",
            120, 230, 440,
            60,
            "Satara Kandi Pedha Khoya, Wheat Flour, Butter, Cardamom, Sugar",
            1, 0, 1, 1, 1, 5.0, 215
        ),
        (
            "palekar-nankatai-rich-rose",
            "bakery-cookies",
            "Palekar Nankatai (Rich Rose)",
            "पालेकर नानकटाई (रिच रोज)",
            "Traditional Indian shortbread cookies scented with Damascus rose",
            "Melt-in-mouth traditional desi ghee nankatai infused with soothing rose aroma. Crumbles delicately with royal nostalgia.",
            "/static/images/official/palekar-nankatai-rich-rose-21.jpg",
            "Rose Aroma",
            110, 210, 400,
            60,
            "Gram Flour, Wheat Flour, Desi Ghee, Pure Rose Essence, Sugar, Cardamom",
            1, 0, 0, 0, 1, 4.8, 85
        ),
        (
            "palekar-nankatai-blissful-butter",
            "bakery-cookies",
            "Palekar Nankatai (Blissful Butter)",
            "पालेकर नानकटाई (बटर)",
            "Rich buttery traditional golden nankatai cookies",
            "Classic grandmother-style baked shortbread made with pure butter and cardamom. Mildly sweet and crumbly.",
            "/static/images/official/palekar-nankatai-blissful-butter-28.jpg",
            "Classic Recipe",
            110, 210, 400,
            60,
            "Wheat Flour, Pure Butter, Sugar, Cardamom Powder",
            1, 0, 0, 0, 1, 4.8, 92
        ),
        (
            "mawa-cake",
            "bakery-cookies",
            "Authentic Fresh Mawa Cake",
            "अस्सल मावा केक",
            "Traditional Parsi-style rich cake baked with pure buffalo milk mawa",
            "Dense, moist, cardamom-scented sponge cake loaded with pure mawa and topped with slivered almonds. Baked fresh in Satara.",
            "/static/images/official/mawa-cake-8.jpg",
            "Fresh Bake",
            130, 250, 480,
            15,
            "Pure Buffalo Milk Mawa, Flour, Butter, Cardamom, Almonds, Sugar",
            1, 0, 1, 0, 1, 4.9, 180
        ),
        (
            "chocolate-cookies",
            "bakery-cookies",
            "Rich Cocoa Chocolate Cookies",
            "रिच चॉकलेट कुकीज",
            "Crunchy baked biscuits loaded with rich cocoa and chocolate chips",
            "A delight for chocolate lovers! Deep cocoa flavors combined with crunchy buttery baked biscuit texture.",
            "/static/images/official/chocolate-cookies-12.jpg",
            "Choco Delight",
            110, 210, 400,
            60,
            "Wheat Flour, Pure Cocoa, Butter, Chocolate Bits, Sugar",
            0, 0, 0, 0, 1, 4.7, 75
        ),
        (
            "tutti-frutti-cookies",
            "bakery-cookies",
            "Colorful Tutti Frutti Cookies",
            "टुटी फ्रुटी कुकीज",
            "Crunchy nostalgic cookies speckled with candied fruit papaya bits",
            "Bright, cheerful, and crisp cookies studded with colorful candied papaya fruit morsels.",
            "/static/images/official/tutti-frutti-cookies-46.jpg",
            "Fruity Crunch",
            100, 190, 360,
            60,
            "Flour, Candied Tutti Frutti Bits, Butter, Sugar, Vanilla",
            0, 0, 0, 0, 1, 4.7, 65
        ),

        # --- 6. FRUIT SQUASHES & SYRUPS ---
        (
            "special-rose-syrup",
            "syrups-squash",
            "Special Rose Sharbat Syrup",
            "स्पेशल रोज सिरप (गुलाब सरबत)",
            "Cooling traditional rose syrup made with Damascus rose extracts",
            "Pure fragrant rose syrup for chilled milk, iced water, mocktails, and faloodas. Instant refreshing coolness for hot summer afternoons.",
            "/static/images/official/special-rose-syrup-3.jpg",
            "Summer Cooler",
            140, 260, 480,
            180,
            "Purified Water, Sugar, Natural Rose Extracts, Citric Acid",
            0, 0, 1, 0, 1, 4.9, 150
        ),
        (
            "special-khus-syrup",
            "syrups-squash",
            "Special Cooling Khus Syrup",
            "स्पेशल खस सिरप",
            "Authentic vetiver grass root extract syrup for natural body cooling",
            "Made from natural wild khus (vetiver roots). Offers an earthy, soothing fragrance known in Ayurveda to reduce body heat.",
            "/static/images/official/special-khus-syrup-15.jpg",
            "Ayurvedic Cooling",
            150, 280, 520,
            180,
            "Natural Khus (Vetiver) Extract, Sugar, Purified Water, Citric Acid",
            0, 0, 0, 0, 1, 4.8, 95
        ),
        (
            "lemon-pudina-fruit-squash",
            "syrups-squash",
            "Lemon Pudina Fruit Squash",
            "लिंबू पुदिना फ्रूट स्क्वॅश",
            "Zesty lemon juice and fresh garden mint digestive squash",
            "Tart lemon paired with cooling garden mint leaves. Mix with chilled soda or water for an invigorating digestive cooler.",
            "/static/images/official/lemon-pudina-fruit-squash-1.jpg",
            "Zesty Mint",
            140, 260, 480,
            180,
            "Real Lemon Juice, Mint (Pudina) Extracts, Sugar, Purified Water, Spices",
            0, 0, 1, 0, 1, 4.8, 110
        ),
        (
            "alphonso-mango-fruit-squash",
            "syrups-squash",
            "Ratnagiri Alphonso Mango Fruit Squash",
            "हापूस आंबा फ्रूट स्क्वॅश",
            "100% natural Alphonso mango pulp cordial squash",
            "Capture the authentic taste of Konkan mangoes all year round! Rich mango nectar concentrate made from ripe Devgad/Ratnagiri Hapoos.",
            "/static/images/official/alphonso-mango-fruit-squash-42.jpg",
            "Mango Magic",
            160, 300, 560,
            180,
            "Alphonso Mango Pulp (Min 25%), Sugar, Water, Citric Acid",
            0, 0, 1, 0, 1, 4.9, 140
        ),
        (
            "raw-mango-syrup",
            "syrups-squash",
            "Kairi Panha (Raw Mango) Syrup",
            "कैरी पन्हे सिरप",
            "Traditional Maharashtrian summer cooler with roasted cumin and mint",
            "Authentic spiced raw mango syrup. Just stir with cold water to make instant chilled Kairi Panha without tedious cooking!",
            "/static/images/official/raw-mango-syrup-10.jpg",
            "Kairi Panha",
            140, 260, 480,
            180,
            "Raw Mango Pulp, Jaggery/Sugar, Roasted Cumin, Cardamom, Black Salt",
            0, 0, 0, 0, 1, 4.8, 80
        ),
        (
            "kulfi-falooda-syrup",
            "syrups-squash",
            "Royal Kulfi Falooda Syrup",
            "कुल्फी फालुदा सिरप",
            "Rich creamy syrup with cardamom, saffron, and rabdi notes",
            "The secret behind cafe-style Faloodas! Drizzle over kulfi, milkshakes, ice cream sundaes, or sweet lassi.",
            "/static/images/official/kulfi-falooda-syrup-56.jpg",
            "Dessert Topping",
            150, 280, 520,
            180,
            "Sugar, Water, Cardamom, Saffron Notes, Condensed Milk Flavors",
            0, 0, 0, 0, 1, 4.8, 72
        ),
        (
            "sugar-free-jamun-juice",
            "syrups-squash",
            "Sugar Free Wild Jamun Juice",
            "रान जामुन ज्युस (साखरमुक्त)",
            "Pure wild black plum juice formulated for sugar balance & digestion",
            "100% pure wild Jamun (black plum) extract with zero added sugar. Revered in Ayurveda for maintaining healthy blood sugar levels.",
            "/static/images/official/sugar-free-jamun-juicwe-20.jpg",
            "Health & Diabetic",
            160, 300, 560,
            180,
            "100% Wild Jamun Fruit Pulp, Purified Water, Permitted Preservative",
            0, 1, 1, 0, 1, 4.9, 125
        ),

        # --- 7. PURE JAGGERY & DRY FRUITS ---
        (
            "jaggery-cube-500gms",
            "organic-staples",
            "Pure Kolhapuri Jaggery Cubes (500g)",
            "शुद्ध कोल्हापुरी गूळ वडी (५०० ग्रॅम)",
            "Chemical-free natural sugarcane jaggery cubes",
            "Traditional sulfur-free Kolhapuri gul molded into convenient kitchen cubes. Rich in iron, natural minerals, and rustic caramel flavor.",
            "/static/images/official/jaggery-cube-500gms-19.jpg",
            "100% Chemical Free",
            85, 160, 300,
            180,
            "Pure Sugarcane Juice without harmful chemicals or bleaching agents",
            0, 0, 1, 0, 1, 4.9, 210
        ),
        (
            "jaggery-powder-500gms",
            "organic-staples",
            "Organic Jaggery Powder (500g)",
            "सेंद्रिय गूळ पावडर (५०० ग्रॅम)",
            "Fine golden jaggery powder for daily tea, milk, and sweets",
            "Direct replacement for white refined sugar! Dissolves smoothly in morning tea, coffee, and porridge without curdling milk.",
            "/static/images/official/jaggery-powder-500gms-13.jpg",
            "Daily Health",
            80, 150, 280,
            180,
            "Pure Cane Jaggery Powder, Zero Refined Additives",
            0, 0, 1, 0, 1, 4.8, 175
        ),
        (
            "whole-cashew-nuts",
            "organic-staples",
            "Premium Whole Cashew Nuts W240",
            "प्रीमियम अखंड काजू (W240)",
            "Large, crisp, whole Goan cashew nuts packed with natural sweetness",
            "Jumbo grade W240 whole cashew nuts. Vacuum sealed for peak freshness and crunch.",
            "/static/images/official/whole-cashew-nuts-22.jpg",
            "Jumbo Grade",
            290, 560, 1080,
            180,
            "100% Whole Grade W240 Cashew Nuts",
            0, 0, 1, 1, 1, 5.0, 195
        ),
        (
            "lemongrass-powder-125gms",
            "organic-staples",
            "Sun-Dried Lemongrass Powder (125g)",
            "गवती चहा पावडर (१२५ ग्रॅम)",
            "Fragrant Gavti Chaha powder for authentic Maharashtrian spiced tea",
            "Sun-dried aromatic lemongrass leaves ground to perfection. A pinch infuses your morning chai with heavenly citrus warmth.",
            "/static/images/official/lemongrass-powder-125gms-33.jpg",
            "Aromatic Chai",
            90, 170, 320,
            180,
            "100% Pure Dried Lemongrass Leaves (Cymbopogon)",
            0, 0, 0, 0, 1, 4.8, 110
        )
    ]

    cursor.executemany("""
    INSERT INTO products (
        id, category_id, name, name_mr, tagline, description, image_url, badge,
        price_250g, price_500g, price_1kg, shelf_life_days, ingredients,
        is_pure_ghee, is_sugar_free, is_bestseller, is_festive, in_stock, rating, reviews_count
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products)

    # Serviceable Pincodes
    pincodes = [
        # Satara & Sangli (Origin - Same Day Delivery!)
        ("415001", "Satara", "Maharashtra", 1, 1, 40),
        ("415002", "Satara", "Maharashtra", 1, 1, 40),
        ("415003", "Satara", "Maharashtra", 1, 1, 40),
        ("415004", "Satara", "Maharashtra", 1, 1, 40),
        ("415409", "Sangli", "Maharashtra", 1, 1, 40),

        # Pune (Same Day / Next Day)
        ("411001", "Pune", "Maharashtra", 1, 1, 50),
        ("411002", "Pune", "Maharashtra", 1, 1, 50),
        ("411004", "Pune", "Maharashtra", 1, 1, 50),
        ("411007", "Pune", "Maharashtra", 1, 1, 50),
        ("411014", "Pune", "Maharashtra", 1, 1, 50),
        ("411028", "Pune", "Maharashtra", 1, 1, 50),
        ("411038", "Pune", "Maharashtra", 1, 1, 50),
        ("411045", "Pune", "Maharashtra", 1, 1, 50),
        ("411057", "Pune", "Maharashtra", 1, 1, 50),

        # Mumbai, Navi Mumbai, Thane (Next Day Express)
        ("400001", "Mumbai", "Maharashtra", 0, 1, 60),
        ("400014", "Mumbai", "Maharashtra", 0, 1, 60),
        ("400050", "Mumbai", "Maharashtra", 0, 1, 60),
        ("400076", "Mumbai", "Maharashtra", 0, 1, 60),
        ("400601", "Thane", "Maharashtra", 0, 1, 60),
        ("400703", "Navi Mumbai", "Maharashtra", 0, 1, 60),

        # Rest of Maharashtra & Metros (2-3 days Express)
        ("416001", "Kolhapur", "Maharashtra", 0, 2, 60),
        ("422001", "Nashik", "Maharashtra", 0, 2, 60),
        ("431001", "Chhatrapati Sambhajinagar", "Maharashtra", 0, 2, 60),
        ("440001", "Nagpur", "Maharashtra", 0, 2, 70),
        ("560001", "Bengaluru", "Karnataka", 0, 2, 80),
        ("110001", "New Delhi", "Delhi", 0, 3, 90),
        ("500001", "Hyderabad", "Telangana", 0, 2, 80)
    ]

    cursor.executemany("""
    INSERT INTO serviceable_pincodes (pincode, city, state, same_day_available, delivery_days, express_fee)
    VALUES (?, ?, ?, ?, ?, ?)
    """, pincodes)

    # Reviews
    reviews = [
        (
            "satara-kandi-pedha",
            "Anand Kulkarni",
            "Pune",
            5,
            "The authenticity of Mama Pedhewale's Kandi Pedha is unmatched! It tastes exactly like the pedhas my grandfather used to bring from Satara 30 years ago. Pure mawa aroma and perfect sweetness.",
            "2026-08-15",
            1
        ),
        (
            "motichoor-ghee-laddu",
            "Snehal Deshmukh",
            "Mumbai",
            5,
            "Ordered 5 kg motichoor laddus for Ganesh Chaturthi pooja. Each laddu was fragrant with pure cow ghee and saffron, packaged with immense care. Delivery was right on time!",
            "2026-08-28",
            1
        ),
        (
            "shahi-kaju-katli",
            "Rohit Patil",
            "Satara",
            5,
            "Thin, tender, and made with 100% cashews without that cheap milky taste other commercial brands have. Mama Pedhewale is the gold standard of sweets.",
            "2026-08-20",
            1
        ),
        (
            "anjeer-kalakand-barfi",
            "Dr. Meera Joshi",
            "Pune",
            5,
            "My parents are diabetic and finding delicious no-sugar sweets is hard. This Turkish Anjeer Dry Fruit Barfi is a blessing! Pure fig sweetness and crunch of nuts.",
            "2026-08-10",
            1
        )
    ]

    cursor.executemany("""
    INSERT INTO reviews (product_id, customer_name, city, rating, review_text, date, is_featured)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, reviews)

    conn.commit()
    conn.close()
    print("Database seeded successfully with authentic Mama Pedhewale catalog!")

if __name__ == "__main__":
    seed_database()
