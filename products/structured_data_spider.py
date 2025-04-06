import re
from typing import Iterable
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from scrapy import Selector, Spider
from scrapy.http import Response

# from products.categories import PaymentMethods, map_payment
from products.items import Product
from products.linked_data_parser import LinkedDataParser
from products.microdata_parser import MicrodataParser


def extract_image(item, response):
    if image := response.xpath('//meta[@name="twitter:image"]/@content').get():
        item["image"] = image.strip()
        return
    if image := response.xpath('//meta[@name="og:image"]/@content').get():
        item["image"] = image.strip()

def extract_offers(item, response, ld_data):
    # Extract price from (singular)
    # TODO: Arrays
    # {'@type': 'Offer', 
    # 'url': 'https://www.botanic.com/produit/955533/ceanothe.html', 
    # 'priceCurrency': 'EUR', 
    # 'price': 29.99, 
    # 'availability': 'https://schema.org/OutOfStock'}
    item["offers"] = ld_data["offers"]


def get_url(response) -> str:
    if canonical := response.xpath('//link[@rel="canonical"]/@href').get():
        return canonical
    return response.url


class StructuredDataSpider(Spider):
    """
    From a scrapy Response, attempt to extract all JSON LD information.

    Use in conjunction with a `CrawlSpider` or directly call `parse_sd`.

    To search for or omit specific data, set any of the spider attributes for:

    By default the spider only looks for certain `wanted_types`.
    You can change this behaviour by specifying this as a list of your desired types.
    Use either https://validator.schema.org/ or uv run scrapy sd <url> to examine potential structured data available.

    Use either `pre_process_data` or `post_process_item` to add to the core behaviour of this spider.

    If the response contains malformed JSON; an alternative `json_parser` can be specified - ie json5 or chompjs.
    """

    dataset_attributes = {"source": "structured_data"}

    wanted_types = [
        "Product",
        "IndividualProduct"
        # DietarySupplement
        # Drug
        # ProductCollection
        # ProductGroup
        # ProductModel
        # SomeProducts
        # Vehicle
    ]
    # convert_microdata = True
    search_for_image = True
    json_parser = "json"

    def __init__(self):
        for i, wanted in enumerate(self.wanted_types):
            if isinstance(wanted, list):
                self.wanted_types[i] = [LinkedDataParser.clean_type(t) for t in wanted]
            else:
                self.wanted_types[i] = LinkedDataParser.clean_type(wanted)

    def parse(self, response: Response, **kwargs):
        yield from self.parse_sd(response)


    def parse_sd(self, response: Response):  # noqa: C901
        """
        Property	Expected Type	Description
        Properties from Product
        additionalProperty	PropertyValue	A property-value pair representing an additional characteristic of the entity, e.g. a product feature or another characteristic for which there is no matching property in schema.org.

        Note: Publishers should be aware that applications designed to use specific schema.org properties (e.g. https://schema.org/width, https://schema.org/color, https://schema.org/gtin13, ...) will typically expect such data to be provided using those properties, rather than using the generic property/value mechanism.
        aggregateRating	AggregateRating	The overall rating, based on a collection of reviews or ratings, of the item.
        asin	Text  or
        URL	An Amazon Standard Identification Number (ASIN) is a 10-character alphanumeric unique identifier assigned by Amazon.com and its partners for product identification within the Amazon organization (summary from Wikipedia's article).

        Note also that this is a definition for how to include ASINs in Schema.org data, and not a definition of ASINs in general - see documentation from Amazon for authoritative details. ASINs are most commonly encoded as text strings, but the [asin] property supports URL/URI as potential values too.
        audience	Audience	An intended audience, i.e. a group for whom something was created. Supersedes serviceAudience.
        award	Text	An award won by or for this item. Supersedes awards.
        brand	Brand  or
        Organization	The brand(s) associated with a product or service, or the brand(s) maintained by an organization or business person.
        category	CategoryCode  or
        PhysicalActivityCategory  or
        Text  or
        Thing  or
        URL	A category for the item. Greater signs or slashes can be used to informally indicate a category hierarchy.
        color	Text	The color of the product.
        colorSwatch	ImageObject  or
        URL	A color swatch image, visualizing the color of a Product. Should match the textual description specified in the color property. This can be a URL or a fully described ImageObject.
        countryOfAssembly	Text	The place where the product was assembled.
        countryOfLastProcessing	Text	The place where the item (typically Product) was last processed and tested before importation.
        countryOfOrigin	Country	The country of origin of something, including products as well as creative works such as movie and TV content.

        In the case of TV and movie, this would be the country of the principle offices of the production company or individual responsible for the movie. For other kinds of CreativeWork it is difficult to provide fully general guidance, and properties such as contentLocation and locationCreated may be more applicable.

        In the case of products, the country of origin of the product. The exact interpretation of this may vary by context and product type, and cannot be fully enumerated here.
        depth	Distance  or
        QuantitativeValue	The depth of the item.
        funding	Grant	A Grant that directly or indirectly provide funding or sponsorship for this item. See also ownershipFundingInfo.
        Inverse property: fundedItem
        gtin	Text  or
        URL	A Global Trade Item Number (GTIN). GTINs identify trade items, including products and services, using numeric identification codes.

        A correct gtin value should be a valid GTIN, which means that it should be an all-numeric string of either 8, 12, 13 or 14 digits, or a "GS1 Digital Link" URL based on such a string. The numeric component should also have a valid GS1 check digit and meet the other rules for valid GTINs. See also GS1's GTIN Summary and Wikipedia for more details. Left-padding of the gtin values is not required or encouraged. The gtin property generalizes the earlier gtin8, gtin12, gtin13, and gtin14 properties.

        The GS1 digital link specifications expresses GTINs as URLs (URIs, IRIs, etc.). Digital Links should be populated into the hasGS1DigitalLink attribute.

        Note also that this is a definition for how to include GTINs in Schema.org data, and not a definition of GTINs in general - see the GS1 documentation for authoritative details.
        gtin12	Text	The GTIN-12 code of the product, or the product to which the offer refers. The GTIN-12 is the 12-digit GS1 Identification Key composed of a U.P.C. Company Prefix, Item Reference, and Check Digit used to identify trade items. See GS1 GTIN Summary for more details.
        gtin13	Text	The GTIN-13 code of the product, or the product to which the offer refers. This is equivalent to 13-digit ISBN codes and EAN UCC-13. Former 12-digit UPC codes can be converted into a GTIN-13 code by simply adding a preceding zero. See GS1 GTIN Summary for more details.
        gtin14	Text	The GTIN-14 code of the product, or the product to which the offer refers. See GS1 GTIN Summary for more details.
        gtin8	Text	The GTIN-8 code of the product, or the product to which the offer refers. This code is also known as EAN/UCC-8 or 8-digit EAN. See GS1 GTIN Summary for more details.
        hasAdultConsideration	AdultOrientedEnumeration	Used to tag an item to be intended or suitable for consumption or use by adults only.
        hasCertification	Certification	Certification information about a product, organization, service, place, or person.
        hasEnergyConsumptionDetails	EnergyConsumptionDetails	Defines the energy efficiency Category (also known as "class" or "rating") for a product according to an international energy efficiency standard.
        hasGS1DigitalLink	URL	The GS1 digital link associated with the object. This URL should conform to the particular requirements of digital links. The link should only contain the Application Identifiers (AIs) that are relevant for the entity being annotated, for instance a Product or an Organization, and for the correct granularity. In particular, for products:
        A Digital Link that contains a serial number (AI 21) should only be present on instances of IndividualProduct
        A Digital Link that contains a lot number (AI 10) should be annotated as SomeProduct if only products from that lot are sold, or IndividualProduct if there is only a specific product.
        A Digital Link that contains a global model number (AI 8013) should be attached to a Product or a ProductModel.
        Other item types should be adapted similarly.
        hasMeasurement	QuantitativeValue	A measurement of an item, For example, the inseam of pants, the wheel size of a bicycle, the gauge of a screw, or the carbon footprint measured for certification by an authority. Usually an exact measurement, but can also be a range of measurements for adjustable products, for example belts and ski bindings.
        hasMerchantReturnPolicy	MerchantReturnPolicy	Specifies a MerchantReturnPolicy that may be applicable. Supersedes hasProductReturnPolicy.
        height	Distance  or
        QuantitativeValue	The height of the item.
        inProductGroupWithID	Text	Indicates the productGroupID for a ProductGroup that this product isVariantOf.
        isAccessoryOrSparePartFor	Product	A pointer to another product (or multiple products) for which this product is an accessory or spare part.
        isConsumableFor	Product	A pointer to another product (or multiple products) for which this product is a consumable.
        isFamilyFriendly	Boolean	Indicates whether this content is family friendly.
        isRelatedTo	Product  or
        Service	A pointer to another, somehow related product (or multiple products).
        isSimilarTo	Product  or
        Service	A pointer to another, functionally similar product (or multiple products).
        isVariantOf	ProductGroup  or
        ProductModel	Indicates the kind of product that this is a variant of. In the case of ProductModel, this is a pointer (from a ProductModel) to a base product from which this product is a variant. It is safe to infer that the variant inherits all product features from the base model, unless defined locally. This is not transitive. In the case of a ProductGroup, the group description also serves as a template, representing a set of Products that vary on explicitly defined, specific dimensions only (so it defines both a set of variants, as well as which values distinguish amongst those variants). When used with ProductGroup, this property can apply to any Product included in the group.
        Inverse property: hasVariant
        itemCondition	OfferItemCondition	A predefined value from OfferItemCondition specifying the condition of the product or service, or the products or services included in the offer. Also used for product return policies to specify the condition of products accepted for returns.
        keywords	DefinedTerm  or
        Text  or
        URL	Keywords or tags used to describe some item. Multiple textual entries in a keywords list are typically delimited by commas, or by repeating the property.
        logo	ImageObject  or
        URL	An associated logo.
        manufacturer	Organization	The manufacturer of the product.
        material	Product  or
        Text  or
        URL	A material that something is made from, e.g. leather, wool, cotton, paper.
        mobileUrl	Text	The mobileUrl property is provided for specific situations in which data consumers need to determine whether one of several provided URLs is a dedicated 'mobile site'.

        To discourage over-use, and reflecting intial usecases, the property is expected only on Product and Offer, rather than Thing. The general trend in web technology is towards responsive design in which content can be flexibly adapted to a wide range of browsing environments. Pages and sites referenced with the long-established url property should ideally also be usable on a wide variety of devices, including mobile phones. In most cases, it would be pointless and counter productive to attempt to update all url markup to use mobileUrl for more mobile-oriented pages. The property is intended for the case when items (primarily Product and Offer) have extra URLs hosted on an additional "mobile site" alongside the main one. It should not be taken as an endorsement of this publication style.
        model	ProductModel  or
        Text	The model of the product. Use with the URL of a ProductModel or a textual representation of the model identifier. The URL of the ProductModel can be from an external source. It is recommended to additionally provide strong product identifiers via the gtin8/gtin13/gtin14 and mpn properties.
        mpn	Text	The Manufacturer Part Number (MPN) of the product, or the product to which the offer refers.
        negativeNotes	ItemList  or
        ListItem  or
        Text  or
        WebContent	Provides negative considerations regarding something, most typically in pro/con lists for reviews (alongside positiveNotes). For symmetry

        In the case of a Review, the property describes the itemReviewed from the perspective of the review; in the case of a Product, the product itself is being described. Since product descriptions tend to emphasise positive claims, it may be relatively unusual to find negativeNotes used in this way. Nevertheless for the sake of symmetry, negativeNotes can be used on Product.

        The property values can be expressed either as unstructured text (repeated as necessary), or if ordered, as a list (in which case the most negative is at the beginning of the list).
        nsn	Text	Indicates the NATO stock number (nsn) of a Product.
        offers	Demand  or
        Offer	An offer to provide this item—for example, an offer to sell a product, rent the DVD of a movie, perform a service, or give away tickets to an event. Use businessFunction to indicate the kind of transaction offered, i.e. sell, lease, etc. This property can also be used to describe a Demand. While this property is listed as expected on a number of common types, it can be used in others. In that case, using a second type, such as Product or a subtype of Product, can clarify the nature of the offer.
        Inverse property: itemOffered
        pattern	DefinedTerm  or
        Text	A pattern that something has, for example 'polka dot', 'striped', 'Canadian flag'. Values are typically expressed as text, although links to controlled value schemes are also supported.
        positiveNotes	ItemList  or
        ListItem  or
        Text  or
        WebContent	Provides positive considerations regarding something, for example product highlights or (alongside negativeNotes) pro/con lists for reviews.

        In the case of a Review, the property describes the itemReviewed from the perspective of the review; in the case of a Product, the product itself is being described.

        The property values can be expressed either as unstructured text (repeated as necessary), or if ordered, as a list (in which case the most positive is at the beginning of the list).
        productID	Text	The product identifier, such as ISBN. For example: meta itemprop="productID" content="isbn:123-456-789".
        productionDate	Date	The date of production of the item, e.g. vehicle.
        purchaseDate	Date	The date the item, e.g. vehicle, was purchased by the current owner.
        releaseDate	Date	The release date of a product or product model. This can be used to distinguish the exact variant of a product.
        review	Review	A review of the item. Supersedes reviews.
        size	DefinedTerm  or
        QuantitativeValue  or
        SizeSpecification  or
        Text	A standardized size of a product or creative work, specified either through a simple textual string (for example 'XL', '32Wx34L'), a QuantitativeValue with a unitCode, or a comprehensive and structured SizeSpecification; in other cases, the width, height, depth and weight properties may be more applicable.
        sku	Text	The Stock Keeping Unit (SKU), i.e. a merchant-specific identifier for a product or service, or the product to which the offer refers.
        slogan	Text	A slogan or motto associated with the item.
        weight	Mass  or
        QuantitativeValue	The weight of the product or person.
        width	Distance  or
        QuantitativeValue	The width of the item.
        Properties from Thing
        additionalType	Text  or
        URL	An additional type for the item, typically used for adding more specific types from external vocabularies in microdata syntax. This is a relationship between something and a class that the thing is in. Typically the value is a URI-identified RDF class, and in this case corresponds to the use of rdf:type in RDF. Text values can be used sparingly, for cases where useful information can be added without their being an appropriate schema to reference. In the case of text values, the class label should follow the schema.org style guide.
        alternateName	Text	An alias for the item.
        description	Text  or
        TextObject	A description of the item.
        disambiguatingDescription	Text	A sub property of description. A short description of the item used to disambiguate from other, similar items. Information from other properties (in particular, name) may be necessary for the description to be useful for disambiguation.
        identifier	PropertyValue  or
        Text  or
        URL	The identifier property represents any kind of identifier for any kind of Thing, such as ISBNs, GTIN codes, UUIDs etc. Schema.org provides dedicated properties for representing many of these, either as textual strings or as URL (URI) links. See background notes for more details.
        image	ImageObject  or
        URL	An image of the item. This can be a URL or a fully described ImageObject.
        mainEntityOfPage	CreativeWork  or
        URL	Indicates a page (or other CreativeWork) for which this thing is the main entity being described. See background notes for details.
        Inverse property: mainEntity
        name	Text	The name of the item.
        potentialAction	Action	Indicates a potential Action, which describes an idealized action in which this thing would play an 'object' role.
        sameAs	URL	URL of a reference Web page that unambiguously indicates the item's identity. E.g. the URL of the item's Wikipedia page, Wikidata entry, or official website.
        subjectOf	CreativeWork  or
        Event	A CreativeWork or Event about this Thing.
        Inverse property: about
        url	URL	URL of the item.

        Instances of Product may appear as a value for the following properties
        Property	On Types	Description
        fundedItem	Grant	Indicates something directly or indirectly funded or sponsored through a Grant. See also ownershipFundingInfo.
        hasVariant	ProductGroup	Indicates a Product that is a member of this ProductGroup (or ProductModel).
        incentivizedItem	FinancialIncentive	The type or specific product(s) and/or service(s) being incentivized.

        DefinedTermSets are used for product and service categories such as the United Nations Standard Products and Services Code:

        {
            "@type": "DefinedTerm",
            "inDefinedTermSet": "https://www.unspsc.org/",
            "termCode": "261315XX",
            "name": "Photovoltaic module"
        }
        For a specific product or service, use the Product type:

        {
            "@type": "Product",
            "name": "Kenmore White 17" Microwave",
        }
        For multiple different incentivized items, use multiple DefinedTerm or Product.
        isAccessoryOrSparePartFor	Product	A pointer to another product (or multiple products) for which this product is an accessory or spare part.
        isBasedOn	CreativeWork	A resource from which this work is derived or from which it is a modification or adaptation.
        isBasedOnUrl	CreativeWork	A resource that was used in the creation of this resource. This term can be repeated for multiple sources. For example, http://example.com/great-multiplication-intro.html.
        isConsumableFor	Product	A pointer to another product (or multiple products) for which this product is a consumable.
        isRelatedTo	Product  or
        Service	A pointer to another, somehow related product (or multiple products).
        isSimilarTo	Product  or
        Service	A pointer to another, functionally similar product (or multiple products).
        itemOffered	Demand  or
        Offer	An item being offered (or demanded). The transactional nature of the offer or demand is documented using businessFunction, e.g. sell, lease etc. While several common expected types are listed explicitly in this definition, others can be used. Using a second type, such as Product or a subtype of Product, can clarify the nature of the offer.
        itemShipped	ParcelDelivery	Item(s) being shipped.
        material	CreativeWork  or
        Product	A material that something is made from, e.g. leather, wool, cotton, paper.
        orderedItem	Order  or
        OrderItem	The item ordered.
        owns	Organization  or
        Person	Products owned by the organization or person.
        productSupported	ContactPoint	The product or service this support contact point is related to (such as product support for a particular product line). This can be a specific product or product line (e.g. "iPhone") or a general category of products or services (e.g. "smartphones").
        typeOfGood	OwnershipInfo  or
        TypeAndQuantityNode	The product that this structured value is referring to.
        """


        # if self.convert_microdata:
        #     MicrodataParser.convert_to_json_ld(response)
        for ld_item in self.iter_linked_data(response):
            self.pre_process_data(ld_item)
            print(ld_item)
            item = LinkedDataParser.parse_ld(ld_item) # , price_format=self.price_format
            url = get_url(response)

            item['ref'] = ld_item['sku']

            if item["ref"] is None:
                item["ref"] = self.get_ref(url, response)

            if isinstance(item["website"], list):
                if len(item["website"]) > 0:
                    item["website"] = item["website"][0]

            if not item["website"]:
                item["website"] = url
            elif item["website"].startswith("www"):
                item["website"] = "https://" + item["website"]
            elif item["website"].startswith("/"):
                item["website"] = urljoin(response.url, item["website"])

            if self.search_for_image and item.get("image") is None:
                extract_image(item, response)

            if item.get("image") and item["image"].startswith("/"):
                item["image"] = urljoin(response.url, item["image"])

            extract_offers(item, response, ld_item)

            yield from self.post_process_item(item, response, ld_item) or []

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if not ld_obj.get("@type"):
                continue

            types = ld_obj["@type"]

            if not isinstance(types, list):
                types = [types]

            types = [LinkedDataParser.clean_type(t) for t in types]

            for wanted_types in self.wanted_types:
                if isinstance(wanted_types, list):
                    if all(wanted in types for wanted in wanted_types):
                        yield ld_obj
                elif wanted_types in types:
                    yield ld_obj

    def get_ref(self, url: str, response: Response) -> str:
        if hasattr(self, "rules"):  # Attempt to pull a match from CrawlSpider.rules
            for rule in getattr(self, "rules"):
                for allow in rule.link_extractor.allow_res:
                    if match := re.search(allow, url):
                        if len(match.groups()) > 0:
                            return match.group(1)
        elif hasattr(self, "sitemap_rules"):
            # Attempt to pull a match from SitemapSpider.sitemap_rules
            for rule in getattr(self, "sitemap_rules"):
                if match := re.search(rule[0], url):
                    if len(match.groups()) > 0:
                        return match.group(1)
        return url

    def pre_process_data(self, ld_data: dict, **kwargs):
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        """Override with any post-processing on the item."""
        yield item