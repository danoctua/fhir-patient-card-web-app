import asyncio
from fhirpy import AsyncFHIRClient


async def main():
    # Create an instance
    client = AsyncFHIRClient(
        'http://hapi.fhir.org/baseR4',
        authorization='app',
    )

    patients = client.resources('Patient')

    res = await patients.search(birthdate__gt='1944', birthdate__lt='1964').fetch_all()
    print(res)
    # /Patient?birthdate=gt1944&birthdate=lt1964

    patients.search(name__contains='John')
    # /Patient?name:contains=John

    patients.search(name=['John', 'Rivera'])
    # /Patient?name=John&name=Rivera

    patients.search(name='John,Eva')
    # /Patient?name=John,Eva

    patients.search(family__exact='Moore')
    # /Patient?family:exact=Moore

    patients.search(address_state='TX')
    # /Patient?address-state=TX

    patients.search(active=True, _id='id')
    # /Patient?active=true&_id=id

    patients.search(gender__not=['male', 'female'])
    # /Patient?gender:not=male&gender:not=female


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())