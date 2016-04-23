-- SQL to create a table of journals by Triage categories (A, G, E, T)
--   with the cells being the number of papers from each journal selected
--   for that category.

-- first get tmp table w/ journal, triage category (dataset), count
select r.journal, ds._dataset_key, ds.abbreviation, count( *) as "refcount"
into #refTcount
from bib_refs r join bib_dataset_assoc dsa on (r._refs_key = dsa._refs_key )
join bib_dataset ds on (dsa._dataset_key = ds._dataset_key)
where r.year = 2013
and r.journal is not null
group by r.journal, ds._dataset_key, ds.abbreviation
||
select count(distinct journal) from #refTcount
||
-- now build the output table w/ columns for each triage category
select  distinct rc.journal, rcA.refcount as "A&P", rcG.refcount as "GO", rcE.refcount as "Expr", rcT.refcount as Tumor
from #refTcount rc 
left outer join #refTcount rcA on (rc.journal = rcA.journal and rcA._dataset_key = 1002)
left outer join #refTcount rcG on (rc.journal = rcG.journal and rcG._dataset_key = 1005)
left outer join #refTcount rcE on (rc.journal = rcE.journal and rcE._dataset_key = 1004)
left outer join #refTcount rcT on (rc.journal = rcT.journal and rcT._dataset_key = 1007)
order by rc.journal
