select r.journal, count( distinct dsa._refs_key)
from bib_refs r join bib_dataset_assoc dsa 
on (r._refs_key = dsa._refs_key and dsa._dataset_key = 1002)
where r.year = 2013
group by r.journal

select r._refs_key, r.journal
from bib_refs r join bib_dataset_assoc dsa on ( r._refs_key = dsa._refs_key)
and r.year = 2013
and dsa._dataset_key = 1008
order by r.journal


select r.journal, ds._dataset_key, ds.abbreviation, count( *) as "refcount"
from bib_refs r join bib_dataset_assoc dsa on (r._refs_key = dsa._refs_key )
join bib_dataset ds on (dsa._dataset_key = ds._dataset_key)
where r.year = 2013
group by r.journal, ds._dataset_key, ds.abbreviation

