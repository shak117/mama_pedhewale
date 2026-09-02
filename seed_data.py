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
            "खास पेढे",
            "Our legendary slow-cooked caramelized mawa pedhas handcrafted since 1948.",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQiMka1Pm6xvVhkQTwakf5ogzJWXJCOsFbrdyVKB46T9w&s=10",
            1
        ),
        (
            "laddu",
            "Desi Ghee Laddus",
            "शुद्ध तुपातील लाडू",
            "Prepared with 100% pure cow ghee, slow-roasted grains and rich nuts.",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQMStMw0KcR_yP8eXKJjH4L4oWrRr-IFZg8v4QsZrFICA&s=10",
            2
        ),
        (
            "kaju-barfi",
            "Kaju & Dry Fruit Sweets",
            "काजू व सुकामेवा मिठाई",
            "Melt-in-mouth delicacies made from premier grade cashews and exotic nuts.",
            "https://www.google.com/imgres?q=kaju%20and%20dry%20fruits%20img&imgurl=https%3A%2F%2Fmedia.istockphoto.com%2Fid%2F157743163%2Fphoto%2Fmixed-nuts.jpg%3Fs%3D612x612%26w%3D0%26k%3D20%26c%3DRmp4RDyrFpCw6HNfhswLriyxmsAHS4Bdiku7_bA5kUc%3D&imgrefurl=https%3A%2F%2Fwww.istockphoto.com%2Fphotos%2Fdry-fruits-cashews&docid=fSMx8AGtjxLDbM&tbnid=M8lGDmJj-ZbvMM&vet=12ahUKEwiC3O-Jwc-WAxUycGwGHW6QG4AQnPAOegQIPRAA..i&w=408&h=612&hcb=2&ved=2ahUKEwiC3O-Jwc-WAxUycGwGHW6QG4AQnPAOegQIPRAA",
            3
        ),
        (
            "festive",
            "Festive Boxes & Modak",
            "सणासुदीचे खास बॉक्सेस व मोदक",
            "Grand gift boxes, auspicious modaks, and festive assortments for your celebrations.",
            "https://www.google.com/imgres?q=festive%20box%20and%20modaks&imgurl=https%3A%2F%2Flookaside.instagram.com%2Fseo%2Fgoogle_widget%2Fcrawler%2F%3Fmedia_id%3D3958918169364509295&imgrefurl=https%3A%2F%2Fwww.instagram.com%2Fp%2FDbvOgnyjF1M%2F&docid=FmdOsSUPqhLWyM&tbnid=eieXYdB7ZlVaaM&vet=12ahUKEwix4qrCwc-WAxX3cWwGHY9gHq4QnPAOegQIHBAA..i&w=1440&h=1919&hcb=2&ved=2ahUKEwix4qrCwc-WAxX3cWwGHY9gHq4QnPAOegQIHBAA",
            4
        ),
        (
            "namkeen",
            "Traditional Namkeen & Savories",
            "पारंपारिक फरसाण व चिवडा",
            "Crisp, spicy, and authentic Maharashtrian tea-time savory delights.",
            "https://www.google.com/imgres?q=traditional%20namkeen%20and%20savouries&imgurl=https%3A%2F%2Fetimg.etb2bimg.com%2Fphoto%2F114425708.cms&imgrefurl=https%3A%2F%2Fretail.economictimes.indiatimes.com%2Fnews%2Ffood-entertainment%2Fpersonal-care-pet-supplies-liquor%2Ffestive-demand-boosts-sale-of-namkeens-millet-snacks%2F114425695&docid=sRlFK7nvJWpptM&tbnid=xZenWn8T0HXMqM&vet=12ahUKEwih84Pwwc-WAxUWb2wGHVMqNz0QnPAOegQIMRAA..i&w=1200&h=900&hcb=2&ved=2ahUKEwih84Pwwc-WAxUWb2wGHVMqNz0QnPAOegQIMRAA",
            5
        )
    ]

    cursor.executemany("""
    INSERT INTO categories (id, name, name_mr, description, image_url, display_order)
    VALUES (?, ?, ?, ?, ?, ?)
    """, categories)

    products = [
        # Pedhas
        (
            "satara-kandi-pedha",
            "pedha",
            "Satara Special Kandi Pedha",
            "सातारी खास कांडी पेढा",
            "The iconic caramelized dark brown pedha slow-cooked for 8 hours",
            "Our flagship pride! Prepared using thick buffalo milk mawa, slow-roasted in heavy copper vats until deep amber caramelization, seasoned with fragrant green cardamom and sugar grains. Unmatched authentic taste of Satara.",
            "https://www.google.com/imgres?q=satara%20special%20kandi%20pedha&imgurl=https%3A%2F%2Fgangdharmithaiwale.co.in%2Fwp-content%2Fuploads%2F2025%2F05%2F58.png&imgrefurl=https%3A%2F%2Fgangdharmithaiwale.co.in%2Fproduct%2Fkandhi-peda%2F&docid=mFXhC9Lwg38p0M&tbnid=JImcDWDlLA_1bM&vet=12ahUKEwiX07XMws-WAxXxTGwGHdySLqAQnPAOegQIdhAA..i&w=800&h=800&hcb=2&ved=2ahUKEwiX07XMws-WAxXxTGwGHdySLqAQnPAOegQIdhAA",
            "Mama's Signature",
            190, 360, 700,
            20,
            "Pure Buffalo Milk Khoya (Mawa), Sugar, Fresh Green Cardamom, Nutmeg",
            1, 0, 1, 0, 1, 4.9, 184
        ),
        (
            "kesar-malai-pedha",
            "pedha",
            "Royal Kesar Malai Peda",
            "शाही केशर मलाई पेढा",
            "Infused with authentic Kashmiri saffron strands and pistachios",
            "Creamy, melt-in-mouth malai pedha infused with handpicked Kashmiri saffron (kesar), offering a rich golden hue and delicate aroma. Crowned with slivers of Iranian pistachios.",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRGyLx1Yb9s0-u6SYAtt_WBL9qucGvipLijqBT8N_K27Q&s=10",
            "Bestseller",
            220, 420, 820,
            15,
            "Cow Milk Khoya, Pure Kashmiri Kesar, Sugar, Cardamom, Pistachio slivers",
            1, 0, 1, 0, 1, 4.8, 128
        ),
        (
            "white-malai-pedha",
            "pedha",
            "Pure White Malai Peda",
            "शुद्ध पांढरा मलाई पेढा",
            "Velvety soft and mildly sweet traditional fresh pedha",
            "Crafted from freshly condensed milk cream, this velvety smooth pedha has a delicate milky sweetness that dissolves effortlessly on your palate.",
            "https://www.google.com/imgres?q=white%20malai%20pedha&imgurl=https%3A%2F%2Fjoshisweetspune.com%2Fwp-content%2Fuploads%2F2025%2F10%2Fmalai-pedha.jpg&imgrefurl=https%3A%2F%2Fjoshisweetspune.com%2Fshop%2Fmalai-pedha%2F&docid=-eWQYRnmQrgz2M&tbnid=pjImEyzGunMXlM&vet=12ahUKEwiR_My0w8-WAxVkcmwGHWTeM3AQnPAOegQIOxAA..i&w=730&h=600&hcb=2&ved=2ahUKEwiR_My0w8-WAxVkcmwGHWTeM3AQnPAOegQIOxAA",
            "Mild Sweetness",
            180, 340, 660,
            12,
            "Pure Full Cream Milk, Khoya, Fine Sugar, Cardamom",
            1, 0, 0, 0, 1, 4.7, 95
        ),
        (
            "dharwad-brown-peda",
            "pedha",
            "Dharwad Special Brown Peda",
            "धारवाड स्पेशल पेढा",
            "Coated in powdered sugar crystal crust with rich caramelized core",
            "Famous regional recipe featuring dark roasted mawa kneaded to perfection, shaped into oval nuggets and dusted with fine sugar crystal powder for that signature crunch.",
            "https://www.google.com/imgres?q=dharwad%20brown%20pedha&imgurl=http%3A%2F%2Findiasweethouse.in%2Fcdn%2Fshop%2Ffiles%2FDharwadPeda.png%3Fv%3D1718868299&imgrefurl=https%3A%2F%2Findiasweethouse.in%2Fproducts%2Fdharwad-peda-1&docid=E6lptmdYJP04uM&tbnid=BHaPu_AWk5DpSM&vet=12ahUKEwiHkILWw8-WAxVwSmwGHQGfA5cQnPAOegUIgwEQAA..i&w=1000&h=1000&hcb=2&ved=2ahUKEwiHkILWw8-WAxVwSmwGHQGfA5cQnPAOegUIgwEQAA",
            "Heritage Classic",
            195, 370, 720,
            25,
            "Slow-roasted Mawa, Sugar, Desi Ghee, Cardamom powder",
            1, 0, 0, 0, 1, 4.8, 76
        ),
        (
            "alphonso-mango-peda",
            "pedha",
            "Ratnagiri Alphonso Mango Peda",
            "रत्नागिरी हापूस आंबा पेढा",
            "Real Alphonso mango pulp blended with rich mawa",
            "Seasonal delight made with 100% natural GI-tagged Ratnagiri Alphonso mango pulp seamlessly blended with rich khoya. A burst of authentic fruit sunshine.",
            "https://www.google.com/imgres?q=alphanso%20mango%20pedha&imgurl=https%3A%2F%2Flookaside.fbsbx.com%2Flookaside%2Fcrawler%2Fmedia%2F%3Fmedia_id%3D1698868635150662%26get_thumbnail%3D1&imgrefurl=https%3A%2F%2Fwww.facebook.com%2Feasyrecipesbymadhavi%2Fvideos%2Fmango-milkl-peda%2F1698868635150662%2F&docid=53MzIq6Ut0jMjM&tbnid=ejNZnD8zQI5dEM&vet=12ahUKEwjgp77sw8-WAxWNS2wGHbFdKBoQnPAOegQIPxAA..i&w=432&h=768&hcb=2&ved=2ahUKEwjgp77sw8-WAxWNS2wGHbFdKBoQnPAOegQIPxAA",
            "Fruit Special",
            210, 400, 780,
            15,
            "Pure Milk Mawa, Alphonso Mango Pulp, Sugar, Cardamom",
            1, 0, 0, 1, 1, 4.9, 112
        ),

        # Laddus
        (
            "motichoor-ghee-laddu",
            "laddu",
            "Shahi Motichoor Laddu",
            "शाही मोतीचूर लाडू (शुद्ध तूप)",
            "Ultra-fine boondi pearls fried in pure cow ghee",
            "Golden boondi pearls cooked to delicate perfection in 100% Shuddh Desi Ghee, dipped in aromatic saffron-cardamom sugar syrup and tossed with crunchy magajtari (melon seeds).",
            "https://www.tahoorasweets.com/product/motichoor-laddu/?srsltid=AfmBOoo2KxgcEdPfT6AiDURABdNOOCVZ_pVqxD_g9fSd6F_8n2JHNrrF",
            "Festival Favorite",
            190, 360, 700,
            14,
            "Gram Flour (Besan), Pure Cow Desi Ghee, Sugar, Saffron, Cardamom, Melon Seeds",
            1, 0, 1, 1, 1, 4.9, 210
        ),
        (
            "khamang-besan-laddu",
            "laddu",
            "Khamang Besan Laddu (Danedar)",
            "खमंग दाणेदार बेसन लाडू",
            "Coarsely ground roasted besan with generous cow ghee",
            "Grandmother's authentic recipe! Coarse chana dal flour roasted with immense patience over low flame with pure ghee, scented with nutmeg and studded with roasted almond-cashew chunks.",
            "https://www.google.com/imgres?q=besan%20ladoo&imgurl=https%3A%2F%2Fwww.sharmispassions.com%2Fwp-content%2Fuploads%2F2022%2F10%2Fbesan-ladoo1.jpg&imgrefurl=https%3A%2F%2Fwww.sharmispassions.com%2Fbesan-ladoo-besan-laddu-recipe%2F&docid=j9pBxWf1_xNX-M&tbnid=ubt1Z92lPf4thM&vet=12ahUKEwjN65ijxs-WAxUHbWwGHW-AAgwQnPAOegQIORAA..i&w=720&h=1080&hcb=2&ved=2ahUKEwjN65ijxs-WAxUHbWwGHW-AAgwQnPAOegQIORAA",
            "Traditional",
            180, 350, 680,
            30,
            "Coarse Bengal Gram Flour, Pure Desi Ghee, Bura Sugar, Almonds, Cashews, Nutmeg, Cardamom",
            1, 0, 1, 0, 1, 4.8, 142
        ),
        (
            "dink-gond-dryfruit-laddu",
            "laddu",
            "Nutritious Dink (Gond) Laddu",
            "पौष्टिक डिंकाचे लाडू (सुकामेवा)",
            "Immunity boosting winter & health laddu packed with dry fruits",
            "A nourishing powerhouse made with crisp fried edible gum (dink/gond), dates, dry coconut, poppy seeds, cashew nuts, almonds, and dry ginger powder bound with pure ghee.",
            "https://www.google.com/imgres?q=dink%20ladoo&imgurl=https%3A%2F%2Fm.media-amazon.com%2Fimages%2FI%2F51jvYbv1eCL.jpg&imgrefurl=https%3A%2F%2Fwww.amazon.in%2FVedu-Suvidha-Premium-Homemade-Laddus%2Fdp%2FB08X2NKTDP&docid=E8Yfrn2UOAhI9M&tbnid=5rZ4tF6d79cuSM&vet=12ahUKEwj9ubrExs-WAxVpbmwGHXGzMYMQnPAOegQIOBAA..i&w=500&h=418&hcb=2&ved=2ahUKEwj9ubrExs-WAxVpbmwGHXGzMYMQnPAOegQIOBAA",
            "Health & Immunity",
            240, 460, 900,
            45,
            "Edible Gum (Gond), Dry Coconut, Pure Cow Ghee, Dates, Cashews, Almonds, Jaggery/Sugar, Sonth",
            1, 0, 0, 0, 1, 4.9, 89
        ),

        # Kaju & Barfi
        (
            "shahi-kaju-katli",
            "kaju-barfi",
            "Shahi Kaju Katli (Silver Vark)",
            "शाही काजू कतली",
            "Diamond cut thin cashew diamonds crafted with Goan cashews",
            "World-class cashew confection made with zero flour or fillers. Contains 100% premier Goan cashews ground to a velvety consistency with minimal sugar and finished with pure vegetarian silver foil.",
            "https://www.google.com/imgres?q=kaju%20katli&imgurl=https%3A%2F%2Fstatic.toiimg.com%2Fphoto%2F55048826.cms&imgrefurl=https%3A%2F%2Frecipes.timesofindia.com%2Frecipes%2Fkaju-katli%2Frs55048826.cms&docid=uIR5s_Kjn8mtXM&tbnid=PQqBMetrcwMlUM&vet=12ahUKEwiMzeDfx8-WAxXwUGcHHTkSFaAQnPAOegQIRBAA..i&w=650&h=650&hcb=2&ved=2ahUKEwiMzeDfx8-WAxXwUGcHHTkSFaAQnPAOegQIRBAA",
            "Evergreen Star",
            260, 500, 980,
            30,
            "Premium Grade W240 Cashew Nuts, Sugar, Cardamom, Purified Water",
            0, 0, 1, 1, 1, 4.9, 340
        ),
        (
            "anjeer-kalakand-barfi",
            "kaju-barfi",
            "Turkish Anjeer Dry Fruit Barfi",
            "अंजीर ड्रायफ्रूट बर्फी (नो शुगर)",
            "Naturally sweet Turkish figs blended with roasted dry fruits",
            "Zero added refined sugar! Rich Turkish figs cooked gently with chopped Californian almonds, pistachios, and cashew nuts. Delicious guilt-free royal indulgence.",
            "https://www.google.com/imgres?q=anjeer%20kalakadn%20barfi&imgurl=http%3A%2F%2Fshakkr.in%2Fcdn%2Fshop%2Ffiles%2FAnjeer_Kalakand.jpg%3Fv%3D1733338299%26width%3D2048&imgrefurl=https%3A%2F%2Fshakkr.in%2Fproducts%2Fanjeer-kalakand%3Fsrsltid%3DAfmBOorEid2NOgO3wyUct46k36R6_hJ2GlunJcL1pgyrIaknn2kNOzWL&docid=inW0dLBYhhUJTM&tbnid=1CFlAGacJrvwBM&vet=12ahUKEwi6tqyyyM-WAxVSWHADHTRpK7IQnPAOegQIThAA..i&w=1080&h=1080&hcb=2&ved=2ahUKEwi6tqyyyM-WAxVSWHADHTRpK7IQnPAOegQIThAA",
            "100% No Added Sugar",
            280, 540, 1050,
            30,
            "Turkish Dried Figs (Anjeer), Roasted Cashews, Californian Almonds, Iranian Pistachios, Desi Ghee",
            1, 1, 1, 0, 1, 4.9, 115
        ),
        (
            "royal-pista-roll",
            "kaju-barfi",
            "Royal Kaju Pista Roll",
            "शाही काजू पिस्ता रोल",
            "Cashew casing filled with roasted pistachio cardamom core",
            "Stunning dual-layered confection featuring an outer sheath of smooth cashew fudge hugging an emerald green core of ground pistachios and saffron.",
            "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800&auto=format&fit=crop&q=80",
            "Premium Gift",
            270, 520, 1020,
            25,
            "Premium Cashew Nuts, Iranian Pistachios, Sugar, Cardamom, Desi Ghee",
            1, 0, 0, 1, 1, 4.8, 92
        ),

        # Festive & Modak
        (
            "ukdiche-modak-box",
            "festive",
            "Mama's Authentic Ukdiche Modak (Pack of 11)",
            "पारंपारिक उकडीचे मोदक (११ नग)",
            "Steamed fragrant rice flour pouches with fresh coconut jaggery",
            "Hand-pleated steamed modaks made with freshly ground fragrant Basmati/Ambemohar rice flour, packed with juicy freshly grated coconut, Kolhapuri jaggery, cardamom, and nutmeg. Served with pure ghee pouch.",
            "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=800&auto=format&fit=crop&q=80",
            "Bappa's Prasad",
            250, 480, 920,
            3,
            "Ambemohar Rice Flour, Fresh Grated Coconut, Kolhapuri Organic Jaggery, Cow Ghee, Cardamom, Nutmeg",
            1, 0, 1, 1, 1, 5.0, 310
        ),
        (
            "mawa-modak-assorted",
            "festive",
            "Assorted Royal Mawa Modak Box",
            "शाही मावा मोदक बॉक्स",
            "Festive shaped modaks in Kesar, Kandi, and Chocolate Mawa",
            "Beautiful festive gift box containing hand-moulded khoya modaks in three delightful flavors: Satara Kandi, Kashmiri Kesar, and Rich Cocoa.",
            "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=800&auto=format&fit=crop&q=80",
            "Festive Box",
            230, 440, 860,
            18,
            "Pure Khoya, Sugar, Kesar, Cardamom, Natural Cocoa, Desi Ghee",
            1, 0, 1, 1, 1, 4.8, 160
        ),
        (
            "shahi-celebration-hamper",
            "festive",
            "Mama Pedhewale Shahi Hamper",
            "मामा पेढेवाले महा-उत्सव हॅम्पर",
            "Luxury hardbound gift box with 4 signature sweets & diyas",
            "The grandest gift for Diwali, weddings, and milestones. Contains 250g Satara Kandi Pedha, 250g Shahi Kaju Katli, 250g Motichoor Laddu, 250g Anjeer Barfi, plus festive brass diyas.",
            "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=800&auto=format&fit=crop&q=80",
            "Luxury Gift",
            399, 749, 1399,
            25,
            "Assorted Kandi Pedha, Kaju Katli, Motichoor Laddu, Anjeer Barfi in gold foil boxes",
            1, 0, 1, 1, 1, 4.9, 88
        ),

        # Namkeen
        (
            "puneri-bakharwadi",
            "namkeen",
            "Crispy Special Bakharwadi",
            "खमंग स्पेशल बाकरवडी",
            "Crispy fried spirals with sweet, spicy, and tangy coconut masala",
            "Iconic snack with flaky gram-flour pastry rolled around a spicy-sweet core of roasted coconut, sesame seeds, fennel, and Maharashtrian spices. Fried to a golden crunch.",
            "https://images.unsplash.com/photo-1567337710282-00832b415979?w=800&auto=format&fit=crop&q=80",
            "Snack Bestseller",
            110, 200, 380,
            60,
            "Besan, Wheat Flour, Roasted Dry Coconut, Sesame Seeds, Spices, Tamarind, Oil",
            0, 0, 1, 0, 1, 4.8, 175
        ),
        (
            "kolhapuri-poha-chivda",
            "namkeen",
            "Spicy Kolhapuri Poha Chivda",
            "कोल्हापुरी पोहा चिवडा",
            "Thin beaten rice crisps tossed with peanuts and dried coconut slices",
            "Light, crispy, non-greasy beaten rice flakes seasoned with golden fried peanuts, roasted dal, fresh curry leaves, green chillies, and aromatic spice blend.",
            "https://images.unsplash.com/photo-1567337710282-00832b415979?w=800&auto=format&fit=crop&q=80",
            "Light Snack",
            95, 180, 340,
            60,
            "Thin Poha (Flattened Rice), Peanuts, Roasted Chana Dal, Curry Leaves, Spices, Oil",
            0, 0, 0, 0, 1, 4.7, 130
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
