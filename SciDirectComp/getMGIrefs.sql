-- Get all refs from MGI for 2013 including their J#, pubmed ID, DOI, and a column
--   for each triage category:  A_P, GO, Expr, Tumor
--set rowcount 100
--||
select r.title, r.title2, r.authors, r.authors2, r.journal, r.vol, r.issue,
        r.date, r.year, r.pgs, r._primary as firstAuthor,
        a.accid as Jnum, p.accid as pubmed, d.accid as DOI,
        (CASE WHEN dsa._dataset_key = Null THEN "false" ELSE "true" END) as A_P,
        (CASE WHEN dsg._dataset_key = Null THEN "false" ELSE "true" END) as GO,
        (CASE WHEN dse._dataset_key = Null THEN "false" ELSE "true" END) as Expr,
        (CASE WHEN dst._dataset_key = Null THEN "false" ELSE "true" END) as Tumor
from bib_refs r  inner join acc_accession a on
  (a._object_key = r._refs_key and a._logicaldb_key = 1 and a.prefixpart = "j:")
    left outer join acc_accession p on
    (p._object_key = r._refs_key and p._logicaldb_key = 29) -- pubmed
    left outer join acc_accession d on
    (d._object_key = r._refs_key and d._logicaldb_key = 65) -- doi
    left outer join bib_dataset_assoc dsa on
    (r._refs_key = dsa._refs_key and dsa._dataset_key = 1002) -- A_P
    left outer join bib_dataset_assoc dsg on
    (r._refs_key = dsg._refs_key and dsg._dataset_key = 1005) -- GO
    left outer join bib_dataset_assoc dse on
    (r._refs_key = dse._refs_key and dse._dataset_key = 1004) -- Expr
    left outer join bib_dataset_assoc dst on
    (r._refs_key = dst._refs_key and dst._dataset_key = 1007) -- Tumor
where r.year = 2013
