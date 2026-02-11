#!/usr/bin/env python3
# dummy_reviews.py
import json
import time
import os
import requests
from datetime import datetime

def get_payload():
    out = [
        {
            "review_title": "Everything looks beautiful, but it feels empty.",
            "review_rating": 6,
            "review_author": "MovimanBond",
            "review_date": "18 dic 2025",
            "review_text": (
                "If you've seen the first two installments, the third is unlikely to surprise you. What we get once again is flawless, mesmerizing visuals stretched across nearly three hours of screen time, accompanied by familiar characters, predictable dramaturgy, and a storyline reduced to almost primitive straightforwardness.\n\n"
                "Yes, the film still boasts a strong, star-studded cast. And yes, the director remains one of the most influential visionaries in the history of cinema. However, there is a lingering sense that Cameron is operating on inertia here: there is little genuine novelty, no truly unexpected midpoint turn, and no tightly constructed narrative twist. The story unfolds along tracks that are easy to anticipate.\n\n"
                "As a result, the film becomes an attraction of visual perfection rather than a true dramatic breakthrough. One can't shake the feeling that the franchise is being deliberately stretched indefinitely, relying almost exclusively on technological superiority.\n\n"
                "Conclusion: I would recommend this film primarily to devoted Avatar fans and lovers of visually driven cinema who are content to spend three hours simply admiring Pandora and the sheer scale of Cameron's craftsmanship. For everyone else, unfortunately, it's something they've already seen in the previous two films."
            ),
        },
        {
            "review_title": "Thanks for seeing me, Jim!",
            "review_rating": 8,
            "review_author": "DreamTinder",
            "review_date": "2 gen 2026",
            "review_text": (
                "Like many others, I have also been irritated by James Cameron's often blunt dialogue: \"unobtanium,\" the persistent \"bro\" and \"cuz,\" and other remnants of a flattened Earth vernacular. In 'Fire and Ash', we are even treated to a \"high four,\" suggesting that Jake Sully has managed to export some of the most annoying aspects of human culture to Pandora. On the plus side, Sigourney Weaver got to say a variation of a line of hers from 'Aliens', which was a nice little Easter egg.\n\n"
                "Dialogue aside, I believe the overarching narratives of the 'Avatar' films engage with some heavy themes more skillfully than they are often given credit for. It's often been pointed out that the true protagonist of this franchise is Pandora itself, a stand-in for our own living planet. Once this is acknowledged, these movies reveal themselves as Cameron's love letters to Earth, and as meditations on what we forfeit when we choose lives severed from the natural world. Seen through this lens, the story transcends the familiar dichotomy of \"natives versus colonizers\" and becomes a broader critique of modern civilization as a whole, and of how a fragmented, capitalist culture erodes our ability to recognize that we're part of something greater than ourselves.\n\n"
                "I understand that we're all wired differently, but Neytiri's corrosive grief and rage, Kiri's deep anxiety over feelings she cannot fully articulate, and Lo'ak's crushing sense of invisibility all struck deeply personal chords. In these characters, I feel seen in ways few movies have ever managed. I grew up as an odd kid in a cottage surrounded by a wild forest where I found a sense of belonging. As an adult who has never fit into modern society, I have continued to seek meaning in nature whenever possible, trekking and camping alone, even traveling to the Amazon rainforest, where I met indigenous communities and learned a bit about their traditional plant medicines. I have participated in ayahuasca and huachuma ceremonies in appropriate contexts, experiences that further deepened my sense of connection to the living world. Having gone through most of my life feeling like a complete outsider, it's astounding to see how James Cameron has managed to build a successful blockbuster franchise on some quirky themes from my own inner life. For a person like me, these movies aren't merely visual spectacles; they make me feel seen, and they communicate feelings I thought few could ever understand.\n\n"
                "I consider 'Fire and Ash' stronger than 'The Way of Water', both because the dialogue feels a bit more refined than in the previous installments, and because the themes are handled with greater emotional maturity. It's not without its flaws, yet its ambition to engage with themes of this complexity within the framework of a blockbuster is, in itself, commendable. In an era saturated with cinematic spectacle, the 'Avatar' franchise offers something rare: it articulates a longing for a deeper communion with life itself. For that alone, I am grateful for what James Cameron has managed to create. I see you, brother!"
            ),
        },
        {
            "review_title": "An Avatar 2 clone but slightly better",
            "review_rating": 7,
            "review_author": "Gamergurl69",
            "review_date": "17 dic 2025",
            "review_text": (
                "I had a good time with this, but make no mistake: this is just the same movie as the sequel with some slight variation. Again, we have Quaritch as the bad guy playing cat and mouse with Jake. Again, we spend a majority of the movie following a subplot about harvesting a precious liquid from whales (or whatever you call them), which seems like it's tacked on to bring the movie to the 3 hour runtime for no good reason (an Avatar tradition at this point). Again, the finale involves the same characters battling it out in the same circumstances with a frustrating lack of resolution. The first two acts introduced some more darkness and stronger emotional beats than either of the first two movies, and the addition of the Ash people was an interesting take to finally see the bad side of Navi. But the third act just phones it in and goes for the familiar route.\n\n"
                "I'm probably being generous with a 7. The visuals are stunning, as expected, and the action isn't necessarily bad - it's just nothing we haven't seen before."
            ),
        },
        {
            "review_title": "The Way of Water: Part Two",
            "review_rating": 8,
            "review_author": "StormyLines",
            "review_date": "28 dic 2025",
            "review_text": (
                "The Way of Water: Part Two Would've been a much more appropriate title because that's exactly what this movie was. More of the same movie that we got with TWoW... Pros: Entertaining, action packed, stunning visuals, ultimately fun overall, and fun to live inside of the world of Avatar.\n\n"
                "Cons: kind of a bland story, extremely long run time but I personally don't mind a long movie. James Cameron kind of plays it safe with this movie and doesn't take too many risks."
            ),
        },
        {
            "review_title": "A marvel cinematic experience; albeit one that struggles to bring something completely new to the table",
            "review_rating": 8,
            "review_author": "Dvir971",
            "review_date": "17 dic 2025",
            "review_text": (
                "Some time ago in the previous century, James Cameron first developed the idea for the Avatar films. When he realized that the tools available at the time weren't sufficient to fully realize his vision, he refused to compromise and made a decision: to put the project completely on ice until technology caught up with what he had imagined. Over the following years, he focused primarily on technological research, working on innovative filming systems and motion-capture methodologies.\n\n"
                "Only in the 2000s did Cameron bring the project back to life in a technologically groundbreaking process. Following the astronomical success of the first film, Cameron began mapping out an entire saga, spanning multiple films and decades of work, all while developing new technologies that would allow him to expand the world he'd created in innovative new directions. The second film, The Way of Water, was released some 13 years (!) after the first, marking a noticeable shift in approach: less a technological showmanship and more with an emphasis on character and story, with the technology serving as a tool to enhance the experience rather than dominate it.\n\n"
                "Fire and Ash arrives at a point where the technology is fully mature with Cameron completely adept at using it, and the story is ripe and well developed. Unsurprisingly, the film is visually stunning and, in my opinion, absolutely must be seen in an IMAX theater. Given its bloated runtime, it's hard for me to imagine watching this at home on a TV - it would diminish so much of what makes the experience work.\n\n"
                "The issue, however, is that it feels like the technological innovation aspect has reached a saturation point of sorts. The visual spectacle, while impressive, is no longer that far from what we've come to expect from other major blockbusters in recent years - at least in the way it is perceived by the viewer. Anyone who remembers the frenzy surrounding the original film's release in 2009 will recall just how unprecedented it felt at the time, while now we kind of got used to it.\n\n"
                "On the plus side, what's been lost in terms of the original film's jaw-dropping \"wow\" factor is made up for by a level of technical maturity that allows Cameron to fully unleash his unique strengths as an action master. The result is some of the most ambitious and visually stunning action sequences I've seen in quite some time - with long stretches of the film functioning as pure, awe-inducing spectacle.\n\n"
                "Unlike the second film, which opened with a significant time jump, this one picks up exactly where its predecessor left off-for better and for worse. On one hand, it maintains that feeling I love that this is one long, continuous epic rather than a series neatly divided into chapters. On the other hand, the film makes little effort to refresh viewers on key plot details or world-building elements, which may leave audiences who haven't revisited the previous film in a while feeling a bit lost.\n\n"
                "From what I remember, there's noticeably more humor here than in the earlier films, and the story does indeed venture into interesting narrative territory. A lot of characters get more depth, new intriguing characters are added, and the stakes are at an all-time high. At the same time, a lot of it feels familiar, safe, even recycled-and there's a sense that the plot is beginning to circle back on itself. The ending left me desiring something a bit more as well.\n\n"
                "The film lays intriguing groundwork for the (at least additional two) upcoming sequels, and if Cameron takes some of the criticism aimed at the second and third films to heart, there's real potential here for an amazing conclusion.\n\n"
                "This has to be said: as good as the film is, and as much as I genuinely enjoyed it, it is unquestionably too long. Very few films, in my view, justify a runtime of around three hours - and this one pushes past that by roughly a quarter of an additional hour, which feels extremely excessive. It's not that the film is boring, but tighter script editing could have made the experience far smoother for many viewers. The only real upside to watching it at home might be the ability to take breaks - but when a movie reaches the point where a break feels necessary, it's usually a sign that the writer and editor became a little sloppy.\n\n"
                "It may sound like I'm being mostly critical here, but the fact is I really did enjoy the film on the pure \"experience\" level. While far from perfect, it's highly entertaining and presents a sweeping, richly textured story that delivers breathtaking action and visuals that truly shine on the big screen.\n\n"
                "Will I be able to re-watch it soon? Not likely. But James Cameron knows what he is doing, and the initial experience is definitely one to be had. Imagine a big-budget adventure/war film that blends classic sci-fi and fantasy elements - with characters and story in the background that we are invested in for years already.\n\n"
                "Fire and Ash isn't a film that will change your outlook on life - or on cinema, for that matter - but it makes up for that by being a rare kind of spectacle, even by 2025 standards. As the third entry in a planned five-film series, it represents the midpoint of what has effectively become the life's work of a visionary director who has devoted decades of his life to realizing the fruits of his imagination. While it's very enjoyable and succeeds in pushing the story into interesting places, it's also guilty of leaning too heavily on familiar tropes from previous installments, and ultimately feels like it could have been a bit more refined."
            ),
        },
        {
            "review_title": "Another visually rich but a shallow fantasy ride",
            "review_rating": 6,
            "review_author": "sujanfaster",
            "review_date": "21 dic 2025",
            "review_text": (
                "16 years ago, I was visually impressed by James Cameron's Avatar and it was my first 3D movie in the theatre. The movie also had a very old school kind of emotional drama in it. 3 years ago when I watched Avatar: Way of Water, I was stunned by the amazing visuals in IMAX 3D. Hands down, it was my best IMAX 3D experience. But, I walked out of the theatre with an incomplete feeling because of the unconvincing story and screenplay. I was thinking maybe the third part is going to show us something very new and blow our minds again. After watching Avatar: Fire and Ash my expectations were crushed and how.\n\n"
                "When it comes to the technology and all the visual elements in the film, James Cameron hits the home run again. There are some new kinds of action sequences in the first half of this very long movie. But somewhere in the middle the movie halts and goes back to all the sides preparing for the 'big war' again and that's where the movie just starts to feel very repetitive. If you are asked to randomly watch the climax action sequences of this film and the way of water, there are very few differences to notice. Seeing the title of the movie most of us expected a new world to be introduced like The Way of Water but there is not much new in terms of world building. There is nothing much new to the storyline as well with the movie revolving around bad human vs good alien concept. If you think about both this and the previous movie together, it is just about humans coming for resources attacking the Na'vi and the wildlife with barely any changes. The first 90 mins of the movie is very crisp and interesting but after that the movie becomes a difficult watch and also very much predictable. The only saving grace for the movie is its visual effects. The effect when the characters are immersed in water is something you'd only see and experience in a good IMAX theatre.\n\n"
                "The other major drawback of this film is its character arc. Apart from one or two characters, almost every character has the same arc in every film. Jake Sully and Colonel Quaritch's battle almost seems like Tom and Jerry at this point. The movie also takes it to an almost funny/friendly side and brings it back to the serious arc without any major reason to do so. While Kiri's character does some interesting stuff in this film, there is a major pay off moment that doesn't feel like one because of how it is portrayed. I was able to think of at least 2 different ways to portray that scene at the spot. Oona Chaplin as Varang is the only stand out performance of this film and her character design is also near perfect. I don't really have a lot to write about other performances and especially that of Jack Champion's Spyder (you can make the assumption).\n\n"
                "Avatar: Fire and Ash is definitely a significant milestone for James Cameron in the visual representation of cinema. But it makes you wonder how many of these fantasy rides you want to continue going to if all makes you feel the same at the end."
            ),
        },
        {
            "review_title": "Not the Best Avatar, but My Favorite",
            "review_rating": 9,
            "review_author": "nillan3",
            "review_date": "17 dic 2025",
            "review_text": (
                "Visually stunning from start to finish, with some of the strongest character moments in the series so far. While Avatar 3 doesn't quite land its central theme as clearly or cohesively as Avatar 2, I ended up enjoying it more overall thanks to how engaging the characters are. Their relationships, conflicts, and quieter moments carried a lot of emotional weight and kept me invested throughout. Avatar 2 is probably the better \"complete package\" in terms of structure and thematic focus, but Avatar 3 won me over by leaning harder into character, which made the experience feel more personal and memorable."
            ),
        },
        {
            "review_title": "Disappointing",
            "review_rating": 6,
            "review_author": "michaelmartins8",
            "review_date": "20 dic 2025",
            "review_text": (
                "Unfortunately, Avatar Fire and Ash lacked what made Avatar (2009) a must see film. Emotional depth and a deep connection to the characters is why we fell in love with Avatar. In Fire and Ash, character motivations seem to be scattered all over the place. The story concentrates primarily around Spider, and his desire to fit in with the rest of the Na'vi. This narrative often times felt weak and struggled to drive the film forward, hitting a wall and slowly disengaging us from the film. I thought James Cameron directed fairly well, giving us great action scenes, while the visuals and sound were also a positive. Ultimately, this film fell short of expectations and leaves you with a mixture of disappointment and frustration."
            ),
        },
        {
            "review_title": "I don't understand the hate",
            "review_rating": 10,
            "review_author": "DraguA-3",
            "review_date": "19 dic 2025",
            "review_text": (
                "So I've watched all the movies, and I simply don't understand what the repetitiveness is all about. This is the story! Humans invading another planet! Na'vi having to fight them! This is the main plot! I loved the first movie, loved the second movie more than the first and this one I simply thought it was incredible! It's not only the visuals, but the story too! I loved getting to know more clans, the fights, the places, the relationships. It has everything: emotion, comedy, tragedy, romance, darkness... What do you mean there is nothing new? I think it has plenty of new things and I think this is the best movie of the franchise yet. I truly hope we will get the rest of the movies."
            ),
        },
        {
            "review_title": "Looks amazing again but still has no story",
            "review_rating": 6,
            "review_author": "marcel-kariton",
            "review_date": "28 dic 2025",
            "review_text": (
                "And btw. The subtitle of the movie is misleading. There is just 5 Minutes Fire and Ash. The movie had to be called Way of the Water 2.\n\n"
                "Spider is the only character that is doing some kind of evolution. The rest of this 3 hours doen't contain any story evolution, any character evolution. James, hire people that knowing how to write real stories!"
            ),
        },
        {
            "review_title": "what happened to all the good writers?",
            "review_rating": 5,
            "review_author": "2Yung4This",
            "review_date": "19 dic 2025",
            "review_text": (
                "I've always had a soft spot for the first *Avatar*. When it came out, I was a kid, and it genuinely felt like something special. The world of Pandora was stunning, the creatures and environments felt alive, and the movie delivered a sense of scale and immersion that very few films had managed at the time. Even though many people criticized the story for borrowing familiar ideas, I never really minded. The execution was strong enough that it still felt fresh and memorable.\n\n"
                "The problem started with the sequel. Waiting 11 years for *The Way of Water* set expectations extremely high, and while the visuals were undeniably impressive, the story felt far too familiar. It was essentially the same conflict, just relocated to a new environment and wrapped around a stronger family-focused narrative. The film looked incredible, but once the initial visual awe wore off, it became clear that the plot wasn't really going anywhere new.\n\n"
                "That's why *Avatar 3* doesn't inspire much confidence for me. From what it seems, the franchise is stuck in a loop: new region of Pandora, new tribe, the same villains, the same themes, and the same structure playing out again. The action scenes are well made, and the CGI is still among the best in the industry, but visuals alone can only carry a movie so far. A great film needs a story that evolves, raises the stakes, and pushes the characters into new territory.\n\n"
                "At this point, the *Avatar* series feels like it's relying too heavily on spectacle while neglecting meaningful narrative progression. If the third movie follows the same pattern as the second, it's hard not to expect the same repetition in the fourth and fifth films as well. The world of Pandora is rich and full of potential, but without a stronger, more daring storyline, the franchise risks becoming visually stunning but emotionally and narratively stagnant."
            ),
        },
        {
            "review_title": "Varang",
            "review_rating": 10,
            "review_author": "JustxRave",
            "review_date": "19 dic 2025",
            "review_text": (
                "I actually really love this movie. I just watched it in the theatre and the whole movie i just couldn't get a minute to go to the toilet, because i was absolutely hooked to the story, probably because i also love the first 2 movies. The new tribe is very interesting and definitely something different, especially Varang, I love her. Go and watch the movie!!"
            ),
        },
        {
            "review_title": "24 or 48 FPS Make Your Mind Up!",
            "review_rating": None,
            "review_author": "mrswarbouys",
            "review_date": "24 dic 2025",
            "review_text": (
                "When the movie started I thought i was actually watching a trailer for a new Avatar game for Xbox or PS5, then i realised to my horror that it was the movie.\n\n"
                "The problem was that the picture looked like the \"soap opera effect\" you get when messing about on your TV, but instead of it being key scenes it kept changing randomly every couple of seconds. I was informed by the cinema staff that it was something to do with the frame rate changing from 24FPS to 48FPS and thats how the director intended it to be.\n\n"
                "WTF? Why? Either have it one way or the other, or even certain scenes, but I dont get why you would want it to change randomly like it does, sorry but i think Cameron has lost the plot. Which brings me on to the run time. 3 and a half hours? Give someone millions of dollars to make a movie and they cant find a half decent script writer or editor to do a good job. Thousands of film students out there looking for work."
            ),
        },
        {
            "review_title": "Spectacular",
            "review_rating": 10,
            "review_author": "Jathin-95",
            "review_date": "26 dic 2025",
            "review_text": (
                "This movie proves that the makers can push their limits in making a masterpiece, this movie concludes what it all started in THE WAY OF WATER, perfect action scenes, remarkable acting, great dialogues, the VFX, it's a beautiful creation, just enjoyed watching it. Do not miss to watch this one, Avatar movie fans must not miss, non avatar movie fans must watch the previous two movies in order to understand this one."
            ),
        },
        {
            "review_title": "It's beautiful but that's it",
            "review_rating": 6,
            "review_author": "robloxworld",
            "review_date": "18 dic 2025",
            "review_text": (
                "I am going to be honest. How can a franchise make 5 billion USD+ (more than the last 8 Marvel Movies combined) yet not making an impact in the film industry besides looking good? I doubt that Cameron has so many things to tell that he needs two more whole new movie for it, cause this movie is over 3 hours, yet it doesn't have any depth to it that would deserve this runtime. It's basically the same plot as Way of Water, no, scratch that, it's Avatar 2's plot that wasn't told in 2 but rather was told in 3 instead.\n\n"
                "Avatar 1-3 is probably going to be an 8 billion franchise by the time it's theatrical run concludes, but a franchise that makes 8 billion does not offer more than a \"Wow, this is beautiful\". When you think of a strong male character, you think of T-800, Luke Skywalker, or even Mad Max, and not Jake Sully. When you think of a strong female character you think of Sarah Connor, Ahsoka, or Furiosa, and not Neytiri. That's what I mean that despite it's success, Avatar does not have the depth, the world, nor offer anything more than the first movie didn't. Sure, I would recommend you watch this in theathre in Imax and one of the few movies that deserve the 3D as well, but once you get out of the theatre... there's no reason to watch this again. When a movie is only good for theathres, and can't be rewatched on it's own, you know that you did something wrong. We are talking about Cameron, who is probably the 2nd best director after Nolan, who revolutionized movies, we can thank him probably all the known franchises, then why didn't he has any idea for a world as colorful as Avatar, I feel by the time Avatar 5 airs, people are going to have enough of this franchise, cause I can't physically imagine someone finishing this and go \"Wow, I can't wait for Avatar 4\"."
            ),
        },
        {
            "review_title": "Best Avatar Movie",
            "review_rating": 10,
            "review_author": "LexiM-56",
            "review_date": "19 dic 2025",
            "review_text": (
                "My sister asked me to come with her to watch the new Avatar. I thought the first two were pretty good, but had no desire to watch the 3rd one at the movie theater. I decided to go because I didn't want my sister to go alone.. and let me tell you! This is one of my top 5 movies of all time. I was engaged every single second. The story line was incredible. It was beyond worth every single second. This is supposed to be a 5 movie series, and it better be just that. If you're one the fence about watching this movie, WATCH IT! This is a must watch! I am not a huge movie lover, and I am in love with this movie."
            ),
        },
        {
            "review_title": "Absolute cinema!",
            "review_rating": 10,
            "review_author": "sven-98893",
            "review_date": "17 dic 2025",
            "review_text": (
                "This is what cinema was made for. Amazing CGI and an immersive world as always in this series, but also the story is surprisingly emotional, even if it clearly has some similaritys to \"The way of water\". For me it was defenitly stronger than the second and approximatly as good ad the first movie. Watch this movie in the best cinema you can, you can't get the full experience at home."
            ),
        },
        {
            "review_title": "Amazing to look at, but way too long",
            "review_rating": 7,
            "review_author": "Fabiesco_",
            "review_date": "17 dic 2025",
            "review_text": (
                "The third chapter of Avatar is stunning, just like the previous ones. Visually it's on another level, with some of the best CGI and world-building you'll see in a cinema. The soundtrack does a lot of heavy lifting too, in my opinion. So the cast does.\n\n"
                "But once again, the length hurts . It feels overstuffed and could easily lose 30-40 minutes without losing anything too important. The story itself is fine, familiar Avatar territory, but it drags in places and starts testing your attention.\n\n"
                "Worth seeing on the biggest screen possible, and 3D, mainly for the spectacle. Just be prepared to sit there for a while."
            ),
        },
        {
            "review_title": "8.5",
            "review_rating": 9,
            "review_author": "jnemarunda",
            "review_date": "17 dic 2025",
            "review_text": (
                "I just watched it, and i have alot of thoughrd mostly positive obviously by my rating Positives: visuals, the new tribe, action, the sully family, colonel quaritch, set up for the next film(if we get it) , world building Mixed:the Humour(theres not many comedy moments but some were funny others were not), some Plotlines felt underveloped, the main antagonist(the fire tribe leader) Negatives:just like with every avatar movie to long (not as bad as the second one tho), the villains(human),the wind tribe lacking screen time and set up, feels like avatar way of water 2 Overall for a avatar movie i think its really good and despite the long run tine and the human villains being(plus the fact itd almost way of water 2) its still fun and enjoy able and i think it is better writen then the other avatar movies (not by alot btw)"
            ),
        },
        {
            "review_title": "Familiar, far too long but also a lot of fun",
            "review_rating": 7,
            "review_author": "eddie_baggins",
            "review_date": "18 dic 2025",
            "review_text": (
                "Far from perfect and far too long, the flaws in James Cameron's third Avatar outing, Fire and Ash are there for all to see and in reality, far from surprising but as per his first two multi-billion dollar outings Cameron's latest visual feast is still a fun and entertaining blockbuster that deserves to put bums on cinema seats.\n\n"
                "Arriving 16 years after Cameron's original Dances with Wolves courtesy of the Blue Man Group box office behemoth dropped into the big screen world, Ash continues on with the pattern the legendary filmmaker set in place with his 3D extravaganza and if anyone is expecting Ash to deliver in the unexpected, they should temper expectations in a major way and learn to just enjoy the ride.\n\n"
                "In a world that seems to find things easier to hate rather than like, Ash could become a bit of a punching bag for those wanting to bemoan the fact Cameron hasn't tried to rewrite the rulebook here but the same naysayers are probably just as likely to have enjoyed the likes of Harry Potter, Lord of the Rings, Star Wars or Marvel's plethora of big screen outings, all franchises and brands that have stuck to what works for better and worse and managed to enthral millions of cinemagoers across the decades.\n\n"
                "Kicking off right where The Way of Water finished, Ash finds Sam Worthington's Jake Sully and Zoe Saldaña's Neytiri struggling to maintain their edge and freedom in the face of growing adversity, adversity that includes their continued battle with Stephen Lang's Quaritch and new adversary Varang, solid new addition Oona Chaplin who brings a fierceness to her fire queen.\n\n"
                "To call Ash's narrative barebones basic would be perfectly acceptable, even kind in many facets and it's a shame that Cameron and his fellow screenwriters Amanda Silver and Rick Jaffa haven't managed to fix the series weakish script work but if people can move past the fact it's always likely the original Avatar was an outlier in regards to it's all round winning ways, Ash much like its predecessor provides much in the way of cinematic joys and spectacle.\n\n"
                "While failing to maximise the addition of the new fire clan led by Varang, who appears set to become the films secondary focus only to be overshadowed by the presence of Quaritch and the impressive performance of Chaplin, Ash still does a lot of things very well including a great opening stretch featuring wind traders and the increasingly stunning special effects work that brings Pandora to life in mesmerising ways, especially in the intended 3D format.\n\n"
                "Releasing at a time and place in movie history where many big-scale films have failed to reach the audience they had hoped for, there's much lying on the shoulders of Cameron and his Na'vi friends to bring joy to the Hollywood universe and cinema chains around the globe, while it's very unlikely that Ash will reach the highs of Avatar or Way of Water, there's enough here to suggest audiences will be happy with what they see and spread the word, encouraging others to make the effort to get back out and partake in the big-screen experience.\n\n"
                "Having listened to Cameron's recent commentary regarding his future plans for the Avatar cinematic space there's a high chance we may have seen the last of a Cameron lead Avatar feature and if that's the case, we can be thankful Cameron did so much for the medium he loves even if he never managed to recapture the lightning in a bottle magic he did with his 2009 launch.\n\n"
                "Final Say -\n\n"
                "Walking a familiar path and dancing to the same beat that's been danced too before, Avatar: Fire and Ash isn't able to reach grand heights but as a fun and visually outstanding big screen spectacle, Cameron proves he is still king.\n\n"
                "3 1/2 helpful vines out of 5."
            ),
        },
        {
            "review_title": "9.5/10",
            "review_rating": 9,
            "review_author": "EbrahimJ-23",
            "review_date": "17 dic 2025",
            "review_text": (
                "This action packed, epic is one of the best movies of the year, and my personal favourite Avatar film. It's over 3 hours long and has some pacing issues, but it's never boring. The ending of the film is what made me love it so much. I'm excited to see the next one, and I am very impressed this is James Cameron's best since Terminator 2."
            ),
        },
        {
            "review_title": "Feels empty and very similar to Avatar 2",
            "review_rating": 6,
            "review_author": "zeratul108",
            "review_date": "12 gen 2026",
            "review_text": (
                "Good: Very pretty, entertaining enough. Good character arcs for Lo'ak, Neytiri, and Varang.\n\n"
                "Bad: pretty is expected, but won't blow you away. Story telling feels kind of aged, characters feel very generic, their motivations, emotions, reactions, are highly predictable. The final conflict feels very forced and underwhelming. They've already done everything they could, and you've seen everything Avatar has to offer in the first two movies.\n\n"
                "This is the worst of the 3 so far. They used the best packaging for a 5.4 movie."
            ),
        },
    ]

    return out

SINK_URL = os.environ.get("SINK_URL", "http://fluentbit:9880/reviewFilm")
DELAY = float(os.environ.get("DELAY", "0.2"))
LOOP = os.environ.get("LOOP", "true").lower() in ("1", "true", "yes")
TIMEOUT = float(os.environ.get("TIMEOUT", "5"))

def send_event(ev: dict):
    payload = dict(ev)
    payload["@timestamp"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    payload["source"] = "boxoffice_static_stub"
    r = requests.post(SINK_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()

def main():
    out = get_payload()
    while True:
        for ev in out:
            send_event(ev)
            # print(ev)
            time.sleep(DELAY)
        if not LOOP:
            break

if __name__ == "__main__":
    main()
