"""
Seed script for audiobook stories

Run this script to add sample English fairy tales to the audiobook_stories collection.
Usage: python scripts/seed_audiobook_stories.py
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.database import Database
from modules.audiobook.repository import audiobook_story_repository


SAMPLE_STORIES = [
    {
        "title": "三只小猪",
        "title_en": "The Three Little Pigs",
        "content": """Once upon a time, there were three little pigs who lived with their mother. One day, their mother said, "You are all grown up now. It's time for you to go out and build your own houses."

The first little pig was lazy. He built his house out of straw. It was quick and easy, but not very strong. "This will do just fine," he said.

The second little pig was a bit more careful. He built his house out of sticks. It took a little longer, but he was proud of his work. "This is a good house," he thought.

The third little pig was the smartest. He built his house out of bricks. It took a long time, but he knew it would be strong and safe. "This house will protect me from anything," he said.

One day, a big bad wolf came to the village. He was hungry and wanted to eat the three little pigs. He went to the first pig's house made of straw.

"Little pig, little pig, let me come in!" said the wolf.
"Not by the hair on my chinny chin chin!" said the first pig.
"Then I'll huff, and I'll puff, and I'll blow your house down!"

And the wolf huffed and puffed and blew the straw house down. The first pig ran to his brother's stick house.

The wolf followed and said, "Little pigs, little pigs, let me come in!"
"Not by the hair on our chinny chin chins!" said the two pigs.
"Then I'll huff, and I'll puff, and I'll blow your house down!"

And the wolf huffed and puffed and blew the stick house down too. Both pigs ran to their brother's brick house.

The wolf arrived at the brick house. "Little pigs, little pigs, let me come in!"
"Not by the hair on our chinny chin chins!" said all three pigs.
"Then I'll huff, and I'll puff, and I'll blow your house down!"

The wolf huffed and puffed, but he could not blow down the brick house. He tried and tried, but the house was too strong.

The wolf had an idea. He would climb down the chimney! But the third little pig was clever. He put a big pot of water on the fire. When the wolf came down the chimney, he fell right into the hot water!

The wolf ran away and never came back. The three little pigs lived happily ever after in the strong brick house. And they learned that hard work always pays off in the end.""",
        "language": "en",
        "category": "fairy_tale",
        "age_group": "3-5",
        "estimated_duration": 180,
        "is_published": True,
        "sort_order": 1
    },
    {
        "title": "金发女孩和三只熊",
        "title_en": "Goldilocks and the Three Bears",
        "content": """Once upon a time, there was a little girl named Goldilocks. She had beautiful golden hair. One day, she was walking in the forest when she found a little house.

The house belonged to three bears: Papa Bear, Mama Bear, and Baby Bear. But they weren't home. They had gone for a walk while their porridge cooled down.

Goldilocks was curious, so she went inside. On the table, she saw three bowls of porridge.

She tasted the porridge from the first bowl. "This porridge is too hot!" she said. She tasted the porridge from the second bowl. "This porridge is too cold!" she said. She tasted the porridge from the third bowl. "Ah, this porridge is just right!" And she ate it all up.

Then Goldilocks saw three chairs. She sat in the first chair. "This chair is too big!" she said. She sat in the second chair. "This chair is too big, too!" she said. She sat in the third chair. "Ah, this chair is just right!" But she sat down so hard that the chair broke into pieces.

Goldilocks was tired, so she went upstairs to the bedroom. She lay down on the first bed. "This bed is too hard!" she said. She lay down on the second bed. "This bed is too soft!" she said. She lay down on the third bed. "Ah, this bed is just right!" And she fell fast asleep.

Soon, the three bears came home from their walk. They looked at the table.

"Someone's been eating my porridge!" said Papa Bear in his great big voice.
"Someone's been eating my porridge!" said Mama Bear in her medium voice.
"Someone's been eating my porridge and ate it all up!" cried Baby Bear in his little voice.

Then they looked at the chairs.

"Someone's been sitting in my chair!" said Papa Bear.
"Someone's been sitting in my chair!" said Mama Bear.
"Someone's been sitting in my chair and broke it!" cried Baby Bear.

They went upstairs to the bedroom.

"Someone's been sleeping in my bed!" said Papa Bear.
"Someone's been sleeping in my bed!" said Mama Bear.
"Someone's been sleeping in my bed and she's still there!" cried Baby Bear.

Just then, Goldilocks woke up. She saw the three bears looking at her. She jumped out of the bed and ran out of the house as fast as she could. She ran all the way home and never went back to that part of the forest again.

And the three bears lived happily ever after.""",
        "language": "en",
        "category": "fairy_tale",
        "age_group": "3-5",
        "estimated_duration": 180,
        "is_published": True,
        "sort_order": 2
    },
    {
        "title": "龟兔赛跑",
        "title_en": "The Tortoise and the Hare",
        "content": """Once upon a time, there was a hare who was very proud of how fast he could run. He would always make fun of the slow tortoise.

"Look at you, slowpoke!" the hare would laugh. "You're so slow, you'll never get anywhere!"

The tortoise was patient and kind. One day, he had enough of the hare's teasing. "I challenge you to a race," said the tortoise calmly.

The hare laughed and laughed. "You? Race me? That's the funniest thing I've ever heard! But okay, I accept. This will be so easy!"

All the forest animals gathered to watch the race. The fox was chosen to be the judge. "On your marks, get set, go!" shouted the fox.

The hare zoomed off like lightning, leaving the tortoise far behind. After running for a while, the hare looked back. The tortoise was nowhere in sight.

"Ha! That silly tortoise is so far behind," thought the hare. "I have plenty of time to take a little nap."

So the hare lay down under a shady tree and soon fell fast asleep.

Meanwhile, the tortoise kept walking. Step by step, he moved forward. He didn't stop to rest. He didn't give up. He just kept going, slow and steady.

The sun moved across the sky. The hare slept on and on.

Finally, the tortoise passed the sleeping hare. He was getting closer to the finish line!

Just then, the hare woke up. He stretched and yawned. "Time to win this race," he said with a smile. But when he looked ahead, he couldn't believe his eyes!

The tortoise was almost at the finish line!

The hare ran as fast as he could, but it was too late. The tortoise crossed the finish line first!

All the animals cheered for the tortoise. He had won the race!

The hare hung his head in shame. He learned an important lesson that day.

"Slow and steady wins the race," said the tortoise with a smile.

From that day on, the hare never made fun of the tortoise again. And he never forgot that it's not about being the fastest, but about never giving up.""",
        "language": "en",
        "category": "fable",
        "age_group": "3-5",
        "estimated_duration": 150,
        "is_published": True,
        "sort_order": 3
    },
    {
        "title": "小红帽",
        "title_en": "Little Red Riding Hood",
        "content": """Once upon a time, there was a sweet little girl who was loved by everyone. Her grandmother gave her a red velvet hood, and she loved it so much that she wore it all the time. Everyone called her Little Red Riding Hood.

One day, her mother said, "Little Red Riding Hood, your grandmother is sick. Please take this basket of food to her. But remember, stay on the path and don't talk to strangers!"

"I will, Mother," said Little Red Riding Hood.

Little Red Riding Hood walked through the forest. The birds were singing, and the flowers were blooming. She was enjoying the beautiful day.

Suddenly, a big wolf appeared. He was very cunning and had a plan.

"Good morning, little girl," said the wolf with a sly smile. "Where are you going?"

Little Red Riding Hood forgot her mother's warning. "I'm going to visit my grandmother. She lives in a house near the big oak tree."

"What a lovely granddaughter you are!" said the wolf. "Why don't you pick some flowers for her?"

Little Red Riding Hood thought this was a wonderful idea. While she picked flowers, the wolf ran ahead to grandmother's house.

The wolf knocked on the door. "It's me, Little Red Riding Hood!" he said in a fake voice.

"Come in, dear," said the grandmother.

The wolf went in and did something very bad. He pretended to be the grandmother by wearing her clothes and getting into her bed.

Soon, Little Red Riding Hood arrived. She knocked on the door.

"Come in, dear," said the wolf in grandmother's voice.

Little Red Riding Hood went in. Something seemed strange about her grandmother.

"Grandmother, what big ears you have!" she said.
"All the better to hear you with, my dear."

"Grandmother, what big eyes you have!"
"All the better to see you with, my dear."

"Grandmother, what big teeth you have!"
"All the better to eat you with!"

Just then, a brave woodcutter heard the commotion. He burst through the door and scared the wolf away. The grandmother came out from where she had been hiding in the closet.

Little Red Riding Hood was safe! She hugged her grandmother and the kind woodcutter.

"Thank you for saving us!" said Little Red Riding Hood.

From that day on, Little Red Riding Hood always listened to her mother. She never talked to strangers again, and she always stayed on the path.

And they all lived happily ever after.""",
        "language": "en",
        "category": "fairy_tale",
        "age_group": "5-8",
        "estimated_duration": 180,
        "is_published": True,
        "sort_order": 4
    },
    {
        "title": "丑小鸭",
        "title_en": "The Ugly Duckling",
        "content": """Once upon a time, a mother duck sat on her eggs, waiting for them to hatch. One by one, the eggs cracked open, and out came beautiful yellow ducklings.

But one egg was bigger than the rest. It took longer to hatch. When it finally opened, out came a large, gray bird.

"Oh my," said the mother duck. "This one looks different."

The gray duckling was bigger than his brothers and sisters. His feathers were gray and messy. The other ducks on the farm laughed at him.

"Look at that ugly duckling!" they quacked. "He doesn't belong here!"

The poor duckling was very sad. He tried to make friends, but everyone was mean to him. Even his brothers and sisters wouldn't play with him.

One day, the ugly duckling decided to run away. He wandered through forests and fields, looking for a place where he belonged.

Winter came, and it was very cold. The ugly duckling was alone and freezing. He found a pond, but the water was turning to ice. He was very weak.

A kind farmer found the duckling and brought him home to get warm. But when spring came, the duckling left to find his place in the world.

The duckling came to a beautiful lake. There, he saw the most magnificent birds he had ever seen. They were white with long, graceful necks. They were swans!

The duckling looked at the water and saw his reflection. He couldn't believe his eyes!

He wasn't an ugly duckling anymore. He had grown into a beautiful white swan!

The other swans swam over to him. "Welcome, beautiful swan!" they said. "Come swim with us!"

The swan was so happy. He finally found where he belonged.

Some children by the lake pointed at him. "Look at that swan! He's the most beautiful one of all!"

The swan remembered all the hard times when he was teased and bullied. But now, he held his head high with pride.

He learned that it doesn't matter what you look like on the outside. What matters is the beautiful creature you become inside.

And the beautiful swan lived happily ever after with his new friends.""",
        "language": "en",
        "category": "fairy_tale",
        "age_group": "5-8",
        "estimated_duration": 180,
        "is_published": True,
        "sort_order": 5
    },
    {
        "title": "狼来了",
        "title_en": "The Boy Who Cried Wolf",
        "content": """Once upon a time, there was a young shepherd boy. His job was to watch over the sheep on the hillside near the village.

The boy was bored. Day after day, he sat on the hill with nothing to do but watch the sheep eat grass. He wished something exciting would happen.

One day, he had an idea. "I know how to have some fun!" he thought.

He ran down to the village shouting, "Wolf! Wolf! A wolf is attacking the sheep!"

All the villagers dropped what they were doing and ran up the hill to help. But when they got there, they found no wolf. The sheep were safe, and the boy was laughing.

"Ha ha! I fooled you!" said the boy. "There's no wolf!"

The villagers were angry. "Don't cry wolf when there's no wolf!" they scolded. They walked back to the village, grumbling.

A few days later, the boy was bored again. He decided to play the same trick.

"Wolf! Wolf!" he cried. "A wolf is chasing the sheep!"

Once again, the villagers ran up the hill to help. And once again, they found no wolf.

"You tricked us again!" they said. "This is not funny!" They were very upset and warned the boy never to do it again.

The boy just laughed and laughed.

Then one day, a real wolf came. It was big and scary, with sharp teeth and hungry eyes. It started chasing the sheep!

"Wolf! Wolf!" the boy screamed. "Please help! A real wolf is here!"

But this time, the villagers didn't come. They thought the boy was lying again.

"He's just playing tricks," they said. "We're not falling for it this time."

The wolf chased away many of the sheep. The boy was very scared and very sorry.

When the villagers finally came to check on him, the boy was crying.

"A wolf really came!" he sobbed. "But no one believed me."

An old man put his hand on the boy's shoulder. "This is what happens when you lie," he said. "Nobody believes a liar, even when they're telling the truth."

The boy learned his lesson that day. He never lied again, and he worked hard to earn back everyone's trust.

And that is why we should always tell the truth.""",
        "language": "en",
        "category": "fable",
        "age_group": "5-8",
        "estimated_duration": 150,
        "is_published": True,
        "sort_order": 6
    }
]


async def seed_stories():
    """Seed sample stories to the database"""
    print("Connecting to database...")
    await Database.connect()

    print("Seeding audiobook stories...")

    for story_data in SAMPLE_STORIES:
        # Check if story already exists
        existing = await audiobook_story_repository.collection.find_one({
            "title_en": story_data["title_en"]
        })

        if existing:
            print(f"  - '{story_data['title_en']}' already exists, skipping")
            continue

        story_id = await audiobook_story_repository.create(story_data)
        print(f"  - Created '{story_data['title_en']}' (id: {story_id})")

    print("\nDone! Seeded audiobook stories successfully.")

    await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(seed_stories())
