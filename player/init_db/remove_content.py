from player.models import Track, Album, Artist


Track.objects.all().delete()
Album.objects.all().delete()
Artist.objects.all().delete()
