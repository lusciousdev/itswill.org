from django.test import TestCase
from .models import *

# Create your tests here.
class MessageProcessingTest(TestCase):
  def setUp(self):
    tuser = TwitchUser.objects.create(
      login = "lusciousdev",
      display_name = "lusciousdev",
      user_id = 82920215
    )
    orecap = OverallRecapData.objects.create(year = 2000, month = 1)
    urecap = UserRecapData.objects.create(overall_recap = orecap, twitch_user = tuser)
    
  def test_message_processing(self):
    overallrecap = OverallRecapData.objects.get(year = 2000, month = 1)
    
    messages = [
      "itswill7 cum",
      "DANKIES musicmakeyoulosecontrol",
      "monkaS monkaW monkaEyes monkaGun! monkaSteer monkaH",
      "VVKool Mini chicken Walk",
      "what's your name?",
      "???",
      "?",
      """MusicMakeYouLoseControl 
⠀⠀⠀⠀⠀⠀⠀⣠⡀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠤⠤⣄⣀⡀⠀⠀⠀⠀⠀⠀⠀ 
⠀⠀⠀⠀⠀⢀⣾⣟⠳⢦⡀⠀⠀⠀⠀⠀⠀⢸Music⠉⠉⠉⠉⠉⠒⣲⡄ 
⠀⠀⠀⠀⠀⣿⣿⣿⡇⡇⡱⠲⢤⣀⠀⠀⠀⢸make ⠀⣠⠴⠊⢹⠁ 
⠀⠀⠀⠀⠀⠘⢻⠓⠀⠉⣥⣀⣠⠞⠀⠀⠀⢸you⢀⡴⠋⠀⠀⠀⢸⠀ 
⠀⠀⠀⠀⢀⣀⡾⣄⠀⠀⢳⠀⠀⠀⠀⠀⠀⢸⢠⡄⢀⡴⠁⠀⠀⠀⠀⠀⡞⠀ 
⠀⠀⠀⣠⢎⡉⢦⡀⠀⠀⡸⠀⠀⠀⠀⠀⢀⡼⣣⠧⡼⠀lose⢠⠇⠀ 
⠀⢀⡔⠁⠀⠙⠢⢭⣢⡚⢣⠀⠀⠀⠀⠀⢀⣇⠁⢸⠁control⢸⠀⠀ 
⠀⡞⠀⠀⠀⠀⠀⠀⠈⢫⡉⠀⠀⠀⠀⢠⢮⠈⡦⠋⠀ MusicMakeYouLoseControl ⠀⣸⠀⠀ 
⢀⠇⠀⠀⠀⠀⠀⠀⠀⠀⠙⢦⡀⣀⡴⠃⠀⡷⡇⢀⡴⠋⠉⠉⠙⠓⠒⠃⠀⠀ 
⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⠀⡼⠀⣷⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ 
⡞⠀⠀⠀⠀⠀⠀⠀⣄⠀⠀⠀⠀⠀⠀⡰⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ 
⢧⠀⠀⠀⠀⠀⠀⠀⠈⠣⣀⠀⠀⡰⠋⠀⠀⠀"""
    ]
    
    for msg in messages:
      overallrecap.process_message(msg, save = False)
      
    overallrecap.save()
    
    self.assertEqual(overallrecap.count_messages, len(messages))
    self.assertEqual(overallrecap.count_cum, 1)
    self.assertEqual(overallrecap.count_chicken, 0)
    self.assertEqual(overallrecap.count_monka, 6)
    self.assertEqual(overallrecap.count_seven, 1)
    self.assertEqual(overallrecap.count_vvkool, 1)
    self.assertEqual(overallrecap.count_mmylc, 3)
    self.assertEqual(overallrecap.count_ascii, 1)
    self.assertEqual(overallrecap.count_q, 2)
    
    userrecap = UserRecapData.objects.get(twitch_user__user_id = 82920215, overall_recap__year = 2000, overall_recap__month = 1)
    
    for msg in messages:
      userrecap.process_message(msg, save = False)
    
    userrecap.save()
      
    self.assertEqual(userrecap.count_messages, len(messages))
    self.assertEqual(userrecap.count_cum, 1)
    self.assertEqual(userrecap.count_chicken, 0)
    self.assertEqual(userrecap.count_monka, 6)
    self.assertEqual(userrecap.count_seven, 1)
    self.assertEqual(userrecap.count_vvkool, 1)
    self.assertEqual(userrecap.count_mmylc, 3)
    self.assertEqual(userrecap.count_ascii, 1)
    self.assertEqual(overallrecap.count_q, 2)