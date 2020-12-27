from cobe.brain import Brain
from config.cobe_config import CONFIG
from apis import pushshift_api, reddit_api
from logs.logger import log
from utils import bytesto, tobytes
import os, sys

class Cobe():
  def __init__(self, config=CONFIG):
    self.ready = False
    self.psapi = pushshift_api
    self.rapi = reddit_api
    self.config = CONFIG
    self.brain = Brain(self.config.get("cobe_main_db"))
    self.size = 0

  def get_reply(self, replyto: str=''):
    if self.ready:
      return self.brain.reply(replyto)
    else:
      log.info(f"cobe not initialized, run init")

  def init(self):
    main_db = self.config.get("cobe_main_db")
    
    # make sure db was initialized correctly
    if os.path.isfile(main_db):
      # set the initial size
      self.size = os.path.getsize(main_db)
      log.info(f"cobe db size is: {str(bytesto(self.size, 'm'))}")
    else:
      log.info(f"cobe db failed to initialize. exiting")
      sys.exit()

    log.debug('filling cobe database for commenting')
    # loop through learning comments until we reach the min db size
    while self.size <= tobytes(self.config.get("cobe_min_db_size")):

      log.info(f"cobe db size is: {str(bytesto(self.size, 'm'))}, need {self.config.get('cobe_min_db_size')} - learning...")
      
      # just learn from random subreddits for now
      subreddit = self.rapi.random_subreddit(nsfw=False)
      
      log.info(f"learning from /r/{subreddit}")
      
      # get the comment generator function from pushshift
      comments = self.psapi.get_comments(subreddit)

      # go through 500 comments per subreddit
      for x in range(500):
        # get the comment from the generator function
        comment = next(comments)
        
        # bot responses are better when it learns from short comments
        if len(comment.body) < 240:
          log.debug(f"learning comment: {comment.body.encode('utf8')}")
          self.brain.learn(comment.body.encode("utf8")) 

      # update the class size variable so the while loop
      # knows when to break
      self.size = os.path.getsize(main_db)

    log.info(f"database min size ({self.config.get('cobe_min_db_size')}) reached")
    self.ready = True