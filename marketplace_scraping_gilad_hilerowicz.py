from selenium import webdriver  # Note selenium must be installed
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from threading import Thread
import json

# program arguments:
MARKETPLACE_NAME = "Ebay"
search_word = "Rolex"
page = 1  # start scrap from this page
last_page = 20  # this is upper bound for page number to be scraped
num_of_threads = 10  # Parallel programming - numbers of threads

# Marketplaces Configuration:
match MARKETPLACE_NAME:
    case "Ebay":
        search_URL = "https://www.ebay.com/sch/i.html?_nkw="
        feed_page_args = "&_pgn="
        results_class = "srp-controls__count-heading"
        item_url_class = "s-item__image"
        description_class = "ux-layout-section__item--table-view"
        price_class = "x-price-primary"
        image_path_class = "ux-image-filmstrip-carousel-item"
        get_itemID = lambda url: url[25:37]  # extract item ID from URL
        error_page_title = 'Error Page | eBay'  # in case item-url is not valid
    case _:
        print("Marketplace is not found")
        quit()


def scrap_page(url, items_urls, driver):
    # step 1: Use the marketplace's search URL to retrieve a set of feed pages
    driver.get(url)
    # checking number of search result > 0:
    results_num = driver.find_element(By.CLASS_NAME, results_class).text
    results_num = int(''.join(x for x in results_num if x.isdigit()))
    if results_num == 0:
        return False  # no more item to scrap
    # step 2: Scrap each feed page to retrieve a list of items URLs.
    items = driver.find_elements(By.CLASS_NAME, item_url_class)
    for item in items:
        item_url = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
        item_url = item_url[:item_url.find('?')]  # cut out irrelevant info (assert item id before '?' in th url)
        items_urls.append(item_url)
    return True


def scrap_item(url, driver):
    driver.get(url)
    item_id = get_itemID(url)
    title = driver.title
    if title == error_page_title:
        return None
    price = driver.find_element(By.CLASS_NAME, price_class).text
    image_path = driver.find_element(By.CLASS_NAME, image_path_class).find_element(By.TAG_NAME,
                                                                                   'img').get_attribute('src')
    description = driver.find_element(By.CLASS_NAME, description_class).text
    return item_id, (title, description, price, image_path)


def save_item(item):
    file_name = MARKETPLACE_NAME + '_' + item[0] + '.jason'
    dict = {
        "title": item[1][0],
        "description": item[1][1],
        "price": item[1][2],
        "image path": item[1][3]
    }
    with open(file_name, "w") as outfile:
        outfile.write(json.dumps(dict, indent=4))


def scraping_thread(item_urls_list, thread_index, total_threads):
    """
    the k-th thread out of n (total_threads), will scrap all items on [(index)mod n == k ] positions
    each item will be scraped and saved (steps 3&4)
    """
    driver = webdriver.Firefox()   # Note this program is using Firefox browser
    index = thread_index
    while index < len(item_urls_list):
        url = item_urls_list[index]
        try:
            item = scrap_item(url,
                              driver)  # step 3: Scrap each product for its title, description, price and image path.
            if item is not None:
                save_item(item)  # step 4: Save each product properties as a JSON file
        except NoSuchElementException:
            try:  # (try again):
                item = scrap_item(url, driver)
                if item is not None:
                    save_item(item)
                    print("2nd try worked")
            except NoSuchElementException:
                print("NoSuchElementException, url: ", url, "item wasn't scraped")
        except Exception as e:
            print("exception- url: ", url, "item wasn't scraped")
            print(e)
        index += total_threads
    driver.close()


# in order to save time steps 1&2 executed simultaneously
items_urls = []
driver1 = webdriver.Firefox()  # Note this program is using Firefox browser
working = True
while working and page <= last_page:
    url = search_URL + search_word + feed_page_args + str(page)
    working = scrap_page(url, items_urls, driver1)  # false -> no more item to scrap
    page += 1
driver1.close()

# starting threading (Parallel programming) for steps 3&4
threads = []
for k in range(num_of_threads):
    t = Thread(target=scraping_thread, args=(items_urls, k, num_of_threads))
    threads.append(t)
    t.start()

for t in threads:  # wait for the threads to complete
    t.join()





