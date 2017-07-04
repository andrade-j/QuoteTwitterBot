import re, tweepy, random, os


class MarkovTwitterBot:

    def __init__(self):
        self.freqDict = {}
        self.lengths = {}

    def create_freq_dict(self, text_list):

        for quote in text_list:
            words = quote.split(' ')
            keys = self.freqDict.keys()
            prev_word = ''
            count = len(words)
            for word in words:
                if not prev_word == '':
                    self.freqDict[prev_word].append(word)

                if word not in keys:
                    self.freqDict.setdefault(word, [])

                prev_word = word

            # Keep track of how long the quotes are.
            if count not in self.lengths.keys():
                self.lengths.setdefault(count, 0)

            self.lengths[count] += 1

            # If there's no subsequent word, delete the word
            for key in list(self.freqDict):
                if self.freqDict[key] == []:
                    del self.freqDict[key]

        return self.freqDict

    def extract_data(self):
        text_file = open('TweetData.txt', 'r', encoding='utf-8')

        data = text_file.readlines()

        first_names = []
        last_names = []
        text_list = []

        for tweet in data:
            if tweet.strip().isdigit():
                continue

            regex = re.compile(r'["“](.*)["”] \W* (\w*)\s?(\w\.)?\s?(\w*)?')
            tweet_data = regex.search(tweet)

            # First, middle and last name
            if tweet_data.group(3) is None:
                first_names.append(str(tweet_data.group(2)))
            else:
                first_names.append(str(tweet_data.group(2)) + ' ' + str(tweet_data.group(3)))

            if not tweet_data.group(4) == '':
                last_names.append(str(tweet_data.group(4)))

            text = tweet_data.group(1)
            text_list.append(''.join(char for char in text if char not in ',:;.?!&'))

        return text_list, first_names, last_names

    def get_tweets(self):
        consumer_key, consumer_secret, access_token, access_token_secret = self.get_twitter_keys()

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth)

        status_list = []
        new_tweets = api.user_timeline(screen_name='CodeWisdom', count=200, include_rts=False)
        status_list.extend(new_tweets)

        while len(new_tweets) > 0:
            lastID = status_list[-1].id - 1
            new_tweets = api.user_timeline(screen_name='CodeWisdom', count=200, include_rts=False, max_id=lastID)
            status_list.extend(new_tweets)

        return status_list

    def save_tweets(self, status_list):

        # Append data if the file already exists
        if os.path.exists('TweetData.txt'):
            mode = 'a'
        else:
            mode = 'w'

        text_file = open('TweetData.txt', mode, encoding='utf-8')

        for status in status_list:
            regex = re.compile(r'["“](.*)["”] \W* (.*)')
            tweet_data = regex.search(status.text)
            if not tweet_data is None:
                text_file.write(tweet_data.group() + '\n')

        # Stamp the file with the id of the newest tweet
        text_file.write(status_list[0].id_str + '\n')
        text_file.close()

    def create_chain(self, freqDict, first_names, last_names):
        # Find the three most common values
        word_avg = [x for x in range(0, 3)]
        for x in word_avg:
            key = max(self.lengths.items())[0]
            del self.lengths[key]
            word_avg[x] = key

        # Choose from the top 3
        length = random.choice(word_avg)

        # Form the sentence
        current_word = random.choice(list(self.freqDict.keys()))
        sentence = current_word
        for x in range(1, length):

            # Make sure another word can be chosen from the dict
            while current_word not in self.freqDict.keys():
                current_word = random.choice(list(self.freqDict.keys()))

            next_word = random.choice(self.freqDict[current_word])
            sentence += ' ' + next_word
            current_word = next_word

        sentence = sentence.capitalize() + '.'

        # Add author of quote
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)

        sentence += ' - ' + first_name + ' ' + last_name

        return sentence

    def get_new_tweets(self):

        file = open('TweetData.txt', 'r', encoding='utf-8')

        # Get the ID of the previous newest tweet
        prev_id = file.readlines()[-1]
        prev_id = int(prev_id.strip())

        # Connect to Twitter account
        consumer_key, consumer_secret, access_token, access_token_secret = self.get_twitter_keys()
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)

        new_tweets = api.user_timeline(screen_name='CodeWisdom', count=200, include_rts=False, max_id=prev_id-1)

        # ID of the most recent tweet posted on the account
        id = new_tweets[0].id

        if id == prev_id:
            # No new tweets
            return
        else:
            status_list = []
            status_list.extend(new_tweets)

        self.save_tweets(status_list)

    def post_tweet(self, tweet):
        consumer_key, consumer_secret, access_token, access_token_secret = self.get_twitter_keys()

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)

        api.update_status(tweet)

    def get_twitter_keys(self):
        consumer_key = ''
        consumer_secret = ''
        access_token = ''
        access_token_secret = ''

        return consumer_key, consumer_secret, access_token, access_token_secret


def main():
    mkbot = MarkovTwitterBot()
    if not (os.path.exists('TweetData.txt')):
        tweets = mkbot.get_tweets()
        mkbot.save_tweets(tweets)

    text, first_names, last_names = mkbot.extract_data()
    freq_dict = mkbot.create_freq_dict(text)
    quote = mkbot.create_chain(freq_dict, first_names, last_names)
    while len(quote) > 140:
        quote = mkbot.create_chain(freq_dict, first_names, last_names)
    mkbot.post_tweet(quote)
    mkbot.get_new_tweets()

if __name__ == '__main__':
    main()
