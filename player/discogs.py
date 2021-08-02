import discogs_client
import jukeoroni.secrets as secrets


# https://github.com/joalla/discogs_client
# https://python3-discogs-client.readthedocs.io


def main():
    d = discogs_client.Client('JukeOroni/0.0.1', user_token=secrets.DISCOGS_USER_TOKEN)
    # results = d.search('The Violin Player', type='release', artist='Vanessa Mae')
    # cover = results[0].images[0]['uri']
    # cover_square = results[0].images[0]['uri150']
    # print(cover)
    # print(cover_square)

    results = d.search('Disturbed', type='artist')
    print(len(results[0].images))
    covers = results[0].images[0]
    for cover in results[0].images:
        print(cover)
    cover_square = results[0].images[0]['uri150']
    print(results[0].images[0].keys())
    print(covers['uri'])
    print(covers['resource_url'])
    print(cover_square)

    # results = d.search('The Sea Sounds of the Earth', artist='David Sun', type='artist')
    # cover = results[0].images[0]['uri']
    # cover_square = results[0].images[0]['uri150']
    # print(cover)
    # print(cover_square)

    return d


if __name__ == '__main__':
    main()

