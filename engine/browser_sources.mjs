import {aspenPurchasedNextResponse} from './aspen_purchased_next_response.mjs';
import {gongyuanImagePage} from './gongyuan_image_page_browser.mjs';
import {scopusAuthorResponse} from './scopus_author_response.mjs';
import {duxiuBooksPage} from './duxiu_books_page_response.mjs';
import {scopusDetailResponse} from './scopus_detail_response.mjs';
import {ebscoMixedPage} from './ebsco_mixed_page_response.mjs';
import {chaoxingJournalsNext} from './chaoxing_journals_next_response.mjs';
import {longyuanMagazinePage} from './longyuan_magazine_page_browser.mjs';
import {airitiThesisPage} from './airiti_thesis_page_response.mjs';
import {cadalSearchPage} from './cadal_search_page_browser.mjs';
import {scienceDirectSearchPage} from './sciencedirect_search_page_browser.mjs';
import {scienceDirectSeriesPage} from './sciencedirect_series_page_browser.mjs';
import {inindexLiteraturePageResponse} from './inindex_literature_page_response.mjs';
import {inindexLiteratureResponse} from './inindex_literature_response.mjs';
import {qingtaMenu,qingtaStatistics} from './qingta_indicator_response.mjs';
import {scopusPageResponse} from './scopus_page_response.mjs';
import {inindexOfficeResponse} from './inindex_office_response.mjs';
import {inindexToponymResponse} from './inindex_toponym_response.mjs';
import {inindexPersonPreview} from './inindex_person_preview_browser.mjs';
import {watsciIssue} from './watsci_issue_browser.mjs';
import {ieeeInstitutionSearch} from './ieee_institution_browser.mjs';
import {iopBooksSearch} from './iop_books_browser.mjs';
import {kluwerLawJournalSearch} from './kluwer_law_journal_browser.mjs';
import {upToDateSearch} from './uptodate_browser.mjs';
import {beckInstitutionSearch} from './beck_institution_browser.mjs';
import {anatomyFootSearch} from './anatomy_foot_search_browser.mjs';
import {anatomyKneeSearch} from './anatomy_knee_search_browser.mjs';
import {anatomyHipSearch} from './anatomy_hip_search_browser.mjs';
import {anatomyPelvisSearch} from './anatomy_pelvis_search_browser.mjs';
import {anatomyHandSearch} from './anatomy_hand_search_browser.mjs';
import {anatomyShoulderSearch} from './anatomy_shoulder_search_browser.mjs';
import {anatomyThoraxSearch} from './anatomy_thorax_search_browser.mjs';
import {anatomySpineSearch} from './anatomy_spine_search_browser.mjs';
import {anatomyHeadNeckSearch} from './anatomy_head_neck_search_browser.mjs';
import {dongfangCatalogResponse} from './dongfang_catalog_browser.mjs';
import {hbnSearchResponse} from './hbn_search_response.mjs';
import {gongyuanImageSearch} from './gongyuan_image_search_browser.mjs';
import {fstaSearchResponse} from './fsta_response_browser.mjs';
import {yuedanSearch} from './lawdata_yuedan_search_browser.mjs';
import {ebscoNursingResponse} from './ebsco_nursing_response.mjs';
import {dynamedSearchResponse} from './dynamed_search_response.mjs';
import {lexisCasesPage} from './lexis_cases_browser.mjs';
import {ebscoMedlineSearch} from './ebsco_medline_cmedm_browser.mjs';
import {ebscoEuropeanAmericasSearch} from './ebsco_european_americas_browser.mjs';
import {rupRss} from './rup_official_rss_browser.mjs';
import {jamaRss} from './jama_official_rss_browser.mjs';
import {emeraldSruSearch} from './emerald_sru_official_browser.mjs';
import {wileySruSearch} from './wiley_sru_official_browser.mjs';
import {hathiBib} from './hathitrust_bib_browser.mjs';
import {zjuTechnologyExpertRecommend} from './zju_tech_agent_experts_browser.mjs';
import {westlawCasesSearch} from './westlaw_cases_browser.mjs';
import {chantSearch} from './chant_institution_browser.mjs';
import {firstSearchResults} from './firstsearch_browser.mjs';
import {merckIndexResults} from './merck_index_browser.mjs';
import {degruyterMathNext} from './degruyter_math_next_browser.mjs';
import {diaolongCatalog} from './diaolong_catalog_browser.mjs';
import {scivalInstitutionSummary} from './scival_summary_browser.mjs';
import {reaxysDocumentsPreview} from './reaxys_preview_browser.mjs';
import {sklibNext} from './sklib_next_browser.mjs';
import {cnkiImageDetail} from './cnki_image_detail_browser.mjs';
import {sklibSearch} from './sklib_search_browser.mjs';
import {cnkiImageSearch} from './cnki_image_browser.mjs';
import {investmentClaimsPage} from './investment_claims_page_browser.mjs';
import {calisJournalsNextResponse} from './calis_journals_next_response.mjs';
import {investmentClaimsSearch} from './investment_claims_browser.mjs';
import {orbisApacQuickResponse} from './orbis_apac_quick_response.mjs';
import {calisJournalsResponse} from './calis_journals_response.mjs';
import {shudiBooksNextResponse} from './shudi_books_next_response.mjs';
import {minguoBooksNextResponse} from './minguo_books_next_response.mjs';
import {rdfybkDetail} from './rdfybk_detail_browser.mjs';
import {rdfybkNextResponse} from './rdfybk_next_response.mjs';
import {shidianBooksNextResponse} from './shidian_books_next_response.mjs';
import {guangzhouDadianNextResponse} from './guangzhou_dadian_next_response.mjs';
import {cxstarBookDetail} from './cxstar_detail_browser.mjs';
import {cxstarNextResponse} from './cxstar_next_response.mjs';
import {tianluNextResponse} from './tianlu_next_response.mjs';
import {theoryResourcesNextResponse} from './theory_resources_next_response.mjs';
import {dingxiuNextResponse} from './dingxiu_next_response.mjs';
import {crggCountryDataResponse} from './crgg_country_data_response.mjs';
import {crggNextResponse} from './crgg_next_response.mjs';
import {overseasHanNextResponse} from './overseas_han_next_response.mjs';
import {inindexNextResponse} from './inindex_next_response.mjs';
import {gpdSelectionNextResponse} from './gpd_selection_next_response.mjs';
import {sunwayReportNextResponse} from './sunway_report_next_response.mjs';
import {digitalFangzhiDetail} from './digital_fangzhi_detail_browser.mjs';
import {digitalFangzhiNext} from './digital_fangzhi_next_browser.mjs';
import {ovidMedlinePage} from './ovid_medline_paged_browser.mjs';
import {jusMundiPaged} from './jus_mundi_paged_browser.mjs';
import {ovidCabPage} from './ovid_cab_paged_browser.mjs';
import {esiFieldsResponse} from './esi_fields_response.mjs';
import {jcrProfileResponse} from './jcr_profile_response.mjs';
import {esiResearchFieldsPage} from './esi_fields_page_reader.mjs';
import {degruyterMathJournals} from './degruyter_math_journals_browser.mjs';
import {jilinNormativeResponse} from './jilin_normative_response.mjs';
import {zhejiangScienceReportsResponse} from './zhejiang_science_reports_response.mjs';
import {longyuanArticlesResponse} from './longyuan_articles_response.mjs';
import {shanghaiScienceReportsResponse} from './shanghai_science_reports_response.mjs';
import {longyuanBookResponse} from './longyuan_books_response.mjs';
import {longyuanMagazineResponse} from './longyuan_magazine_response.mjs';
import {cnbksyResponse} from './cnbksy_response.mjs';
import {rdfybkResponse} from './rdfybk_response.mjs';
import {incitesOrganizationFilterResponse} from './incites_organization_filter_response.mjs';
import {jiangsuLawSearchResponse} from './jiangsu_law_search_response.mjs';
import {incitesOrganizationsResponse} from './incites_organizations_response.mjs';
import {guangzhouDadianResponse} from './guangzhou_dadian_response.mjs';
import {zhangyueResponse} from './zhangyue_response.mjs';
import {crggResponse} from './crgg_response.mjs';
import {cxstarResponse} from './cxstar_response.mjs';
import {dingxiuResponse} from './dingxiu_response.mjs';
import {tianluResponse} from './tianlu_response.mjs';
import {overseasHanResponse} from './overseas_han_response.mjs';
import {historicNewsResponse} from './cnbksy_historic_news_response.mjs';
import {shidianBooksResponse} from './shidian_books_response.mjs';
import {minguoBooksResponse} from './minguo_books_response.mjs';
import {inindexResponse} from './inindex_response.mjs';
import {osirisResponse} from './osiris_response.mjs';
import {ncpssdResponse} from './ncpssd_response.mjs';
import {cadalPosterResponse} from './cadal_poster_response.mjs';
import {cadalHistoricalPhotosResponse} from './cadal_historical_photos_response.mjs';
import {shudiBooksResponse} from './shudi_books_response.mjs';
import {cadalInscriptionsResponse} from './cadal_inscriptions_response.mjs';
import {theoryResourcesResponse} from './theory_resources_response.mjs';
import {cadalAntiqueMapsResponse} from './cadal_antique_maps_response.mjs';
import {digitalFangzhiResponse} from './digital_fangzhi_response.mjs';
import {cadalWartimeResponse} from './cadal_wartime_response.mjs';
import {cadalChiangResponse} from './cadal_chiang_response.mjs';
import {ovidCabSearch} from './ovid_cab_browser.mjs';
import {ovidMedlineSearch} from './ovid_medline_browser.mjs';
import {ovidBiosisSearch} from './ovid_biosis_browser.mjs';
import {ovidLwwBooksCurrent} from './ovid_lww_books_browser.mjs';
import {wanfangFangzhiSearch} from './wanfang_fangzhi_browser.mjs';
import {wanfangVideoSearch} from './wanfang_video_browser.mjs';
import {wanfangSearch} from './wanfang_browser.mjs';
import {wanfangPatentResponse} from './wanfang_patent_response.mjs';
import {wanfangStandardResponse} from './wanfang_standard_response.mjs';
import {wanfangLawResponse} from './wanfang_law_response.mjs';
import {wanfangThesisResponse} from './wanfang_thesis_response.mjs';
import {searchWanfangThesis} from './wanfang_thesis_auto_response.mjs';
import {wanfangPeriodicalResponse} from './wanfang_periodical_response.mjs';
import {searchWanfangPeriodical} from './wanfang_periodical_auto_response.mjs';
import {wanfangConferenceResponse} from './wanfang_conference_response.mjs';
import {searchWanfangConference} from './wanfang_conference_auto_response.mjs';
import {wanfangCstadResponse} from './wanfang_cstad_response.mjs';
import {wanfangNstrResponse} from './wanfang_nstr_response.mjs';
import {wanfangMagazineResponse} from './wanfang_magazine_response.mjs';
import {wanfangFangzhiResponse} from './wanfang_fangzhi_response.mjs';
import {wanfangFangzhiItemResponse} from './wanfang_fangzhi_item_response.mjs';
import {wanfangVideoResponse} from './wanfang_video_response.mjs';
import {wanfangPeriodicalPage2Response} from './wanfang_periodical_page2_response.mjs';
import {airitiEbooksResponse} from './airiti_ebooks_response.mjs';
import {zhizhenConferenceResponse} from './zhizhen_conference_response.mjs';
import {zhizhenLawResponse} from './zhizhen_law_response.mjs';
import {zhizhenNewspaperResponse} from './zhizhen_newspaper_response.mjs';
import {thiemeSearchResponse} from './thieme_search_response.mjs';
import {zhizhenThesisResponse} from './zhizhen_thesis_response.mjs';
import {duxiuBooksResponse} from './duxiu_books_response.mjs';
import {duxiuBookDetail} from './duxiu_book_detail_response.mjs';
import {searchDuxiuBooks} from './duxiu_books_auto_response.mjs';
import {searchIgInstitution} from './igpublish_institution_search_response.mjs';
import {searchJstorInstitution,jstorInstitutionDetail} from './jstor_institution_search_response.mjs';
import {cadalTaiwanResistanceResponse} from './cadal_taiwan_resistance_response.mjs';
import {cadalManuscriptResponse} from './cadal_manuscript_response.mjs';
import {dengkeResponse} from './dengke_response.mjs';
import {pishuPublishDateResponse} from './pishu_publishdate_response.mjs';
import {airitiThesisResponse} from './airiti_thesis_response.mjs';
import {searchCairnResponse} from './cairn-response.mjs';
import {galeScholarLabSearch} from './gale_scholar_lab_browser.mjs';
import {searchEbscoEClassics} from './ebsco-eclassics-session.mjs';
import {cnkiDegreeSearchResponse} from './cnki_degree_response.mjs';
import {searchCnkiDegree} from './cnki_degree_auto_response.mjs';
import {cnkiJournalsResponse} from './cnki_journals_response.mjs';
import {searchCnkiJournals} from './cnki_journals_auto_response.mjs';
import {cnkiNewspapersResponse} from './cnki_newspapers_response.mjs';
import {searchCnkiNewspapers} from './cnki_newspapers_auto_response.mjs';
import {cnkiDomesticConferenceResponse} from './cnki_domestic_conference_response.mjs';
import {searchCnkiDomesticConference} from './cnki_domestic_conference_auto_response.mjs';
import {cnkiInternationalConferenceResponse} from './cnki_international_conference_response.mjs';
import {searchCnkiInternationalConference} from './cnki_international_conference_auto_response.mjs';
import {cnkiSerialsResponse} from './cnki_serials_response.mjs';
import {searchCnkiSerials} from './cnki_serials_auto_response.mjs';
import {cnkiGazetteResponse} from './cnki_gazette_response.mjs';
import {cnkiPartyJournalsResponse} from './cnki_party_journals_response.mjs';
import {cnkiReferenceResponse} from './cnki_reference_response.mjs';
import {cnkiYearbooksResponse} from './cnki_yearbooks_response.mjs';
import {searchCnkiYearbooks} from './cnki_yearbooks_auto_response.mjs';
import {cnkiCultureJournalsResponse} from './cnki_culture_journals_response.mjs';
import {cnkiCitationResponse} from './cnki_citation_response.mjs';
import {wisersResponse} from './wisers_response.mjs';
import {taylorBooksResponse,searchTaylorBooks} from './taylor_books_response.mjs';
import {scopusSessionResponse} from './scopus_session_response.mjs';
import {compendexResponse} from './compendex_response.mjs';
import {searchCompendex} from './compendex_auto_response.mjs';
import {oreillyBooksResponse} from './oreilly_books_response.mjs';
import {aspenPurchasedResponse} from './aspen_purchased_response.mjs';
import {sunwayReportResponse} from './sunway_report_response.mjs';
import {gpdSelectionResponse} from './gpd_selection_response.mjs';
import {cqvipPage2Response} from './cqvip_page2_response.mjs';
import {cqvipPage1Response} from './cqvip_page1_response.mjs';
import {chaoxingBooksPage2Response} from './chaoxing_books_page2_response.mjs';
import {chaoxingBooksPage1Response} from './chaoxing_books_page1_response.mjs';
import {searchMathSciNet} from './mathscinet-session.mjs';
import {searchCNRDS} from './cnrds-session.mjs';
import {fanyanProjectPage} from './fanyan_project_response.mjs';
import {zhilinPolicyResponse} from './zhilin_policy_response.mjs';
import {searchCSMAR} from './csmar-session.mjs';
import {chaoxingJournalsSearch} from './chaoxing_journals_browser.mjs';
import {wenxingeSearch} from './wenxinge_browser.mjs';
import {cnpeBrillSubscribedCurrent} from './cnpe_brill_subscribed_browser.mjs';
import {springerProtocolsCurrent} from './springer_protocols_browser.mjs';
import {springerJetpSearch} from './springer_jetp_browser.mjs';
import {rapidoSearch} from './rapido_browser.mjs';
import {adisDrugsSearch} from './adis_drugs_browser.mjs';
import {embaseCurrentResults} from './embase_browser.mjs';
import {itextWileyBrowse, itextCrcBrowse} from './itext_subsets_browser.mjs';
import {cnkiStatisticalBooksSearch} from './cnki_statistical_books_browser.mjs';
import {shutongwenQhdSearch} from './shutongwen_qhd_browser.mjs';
import {shutongwenStoneSearch} from './shutongwen_stone_browser.mjs';
import {calisYiduSearch} from './calis_yidu_browser.mjs';
import {calisJournalsSearch} from './calis_journals_browser.mjs';
import {cnkiSearch} from './cnki_browser.mjs';
import {pqdtChinaSearch} from './pqdt_china_browser.mjs';
import {cochraneReviewsSearch} from './cochrane_browser.mjs';
import {emeraldBooksSearch} from './emerald_books_browser.mjs';
import {scienceDirectSeriesSearch, scienceDirectBooksSearch} from './sciencedirect_series_browser.mjs';
import {ulrichsSearch} from './ulrichsweb_browser.mjs';
import {iopSearch} from './iop_browser.mjs';
import {orbisMaQuickSearch} from './orbis_ma_browser.mjs';
import {orbisAmericasQuickSearch} from './orbis_americas_browser.mjs';
import {bankfocusQuickSearch} from './bankfocus_browser.mjs';
import {apsPage} from './aps_browser.mjs';
import {jusMundiPage} from './jus_mundi_browser.mjs';
import {maxPlanckInternationalLawPage} from './max_planck_international_law_browser.mjs';
import {oxfordReportsPage, oedDictionaryPage} from './oxford_oril_oed_browser.mjs';
import {mrsAdvancesPage} from './mrs_advances_browser.mjs';
import {proquestPqdtSearch} from './proquest_pqdt_browser.mjs';
import {proquestMarketResearchSearch} from './proquest_market_research_browser.mjs';
import {iglibrarySiamSearch, iglibraryMorganSearch} from './iglibrary_siam_morgan_browser.mjs';
import {iglibraryAstmSearch, iglibraryIecSearch} from './iglibrary_products_browser.mjs';
import {galeDirectorySearch} from './gale_directory_browser.mjs';
import {proquestEeboSearch} from './proquest_eebo_browser.mjs';
import {galeLitfinderSearch} from './gale_litfinder_browser.mjs';
import {galeCriticismSearch} from './gale_criticism_browser.mjs';
import {galeTimesSearch} from './gale_times_browser.mjs';
import {galeOpposingSearch} from './gale_opposing_browser.mjs';
import {galeBusinessSearch} from './gale_business_browser.mjs';
import {galeEccoSearch} from './gale_ecco_browser.mjs';
import {galeLiteratureSearch} from './gale_literature_browser.mjs';
import {galeWorldHistorySearch} from './gale_world_history_browser.mjs';
import {proquestAbiGlobalSearch} from './proquest_abi_global_browser.mjs';
import {proquestAbiDatelineSearch} from './proquest_abi_dateline_browser.mjs';
import {proquestAbiTradeSearch} from './proquest_abi_trade_browser.mjs';
import {proquestBusinessResearchSearch} from './proquest_business_research_browser.mjs';
import {proquestPharmaNewsSearch} from './proquest_pharma_news_browser.mjs';
import {proquestHealthResearchSearch} from './proquest_health_research_browser.mjs';
import {proquestHealthSearch} from './proquest_health_browser.mjs';
import {proquestPaoSearch} from './proquest_pao_browser.mjs';
import {proquestAbiSearch} from './proquest_abi_browser.mjs';
import {proquestResearchLibrarySearch} from './proquest_research_library_browser.mjs';
import {ebscoNewspaperSearch} from './ebsco_newspaper_browser.mjs';
import {ebscoRegionalBusinessSearch} from './ebsco_regional_business_browser.mjs';
import {ebscoMlaDirectorySearch} from './ebsco_mla_directory_browser.mjs';
import {ebscoMathscinetSearch} from './ebsco_mathscinet_browser.mjs';
import {ebscoEnvironmentSearch} from './ebsco_environment_browser.mjs';
import {ebscoTeacherReferenceSearch} from './ebsco_teacher_reference_browser.mjs';
import {ebscoEricSearch} from './ebsco_eric_browser.mjs';
import {ebscoGreenfileSearch} from './ebsco_greenfile_browser.mjs';
import {ebscoListaSearch} from './ebsco_lista_browser.mjs';
import {ebscoDissertationsSearch} from './ebsco_dissertations_browser.mjs';
import {ebscoEbooksSearch} from './ebsco_ebooks_browser.mjs';
import {ebscoMedlineCompleteSearch} from './ebsco_medline_complete_browser.mjs';
import {ebscoDentistrySearch} from './ebsco_dentistry_browser.mjs';
import {ebscoHospitalitySearch} from './ebsco_hospitality_browser.mjs';
import {ebscoMlaSearch} from './ebsco_mla_browser.mjs';
import {ebscoFoodSearch} from './ebsco_food_browser.mjs';
import {ebscoCinahlSearch} from './ebsco_cinahl_browser.mjs';
import {ebscoAcademicPremierSearch} from './ebsco_academic_premier_browser.mjs';
import {ebscoBusinessPremierSearch} from './ebsco_business_premier_browser.mjs';
import {ebscoCommunicationSearch} from './ebsco_communication_browser.mjs';
import {ebscoPsycInfoSearch} from './ebsco_psycinfo_browser.mjs';
import {ebscoEconlitSearch} from './ebsco_econlit_browser.mjs';
import {ebscoPoliticalSearch} from './ebsco_political_browser.mjs';
import {ebscoBriSearch} from './ebsco_bri_browser.mjs';
import {ebscoPsycarticlesSearch} from './ebsco_psycarticles_browser.mjs';
import {ebscoPsychologyCollectionSearch} from './ebsco_psychology_collection_browser.mjs';
import {ebscoBasSearch} from './ebsco_bas_browser.mjs';
import {proquestLionSearch} from './proquest_lion_browser.mjs';
import {lateQingRepublicJournalsSearch} from './late_qing_republic_journals_browser.mjs';
import {airitiThesisSearch} from './airiti_thesis_browser.mjs';
import {cnpeBooksSearch} from './cnpe_books_browser.mjs';
import {gujidhFifthSearch} from './gujidh_fifth_browser.mjs';
import {chaoxingEbooksSearch} from './chaoxing_ebooks_browser.mjs';
import {cnpeReadingSearch} from './cnpereading_browser.mjs';
import {qiushiSearch} from './qiushi_browser.mjs';
import {cssciSearch} from './cssci_browser.mjs';
import {zhonghuaClassicsSearch} from './zhonghua_classics_browser.mjs';
/** 为 Codex CUA 已绑定 Tab 提供统一的单页检索入口。 */
import {cqvipSearch} from './cqvip_browser.mjs';
import {ncpssdSearch} from './ncpssd_browser.mjs';
import {rdfybkSearch} from './rdfybk_browser.mjs';
import {duxiuBookSearch} from './duxiu_browser.mjs';
import {springerPage, sciencePage, musePage, cambridgePage, ebookCentralPage, naturePage, emeraldPage, sagePage, bmjPage, annualReviewsPage, bioonePage, hepJournalsPage, euclidPage, scoap3BooksPage, britannicaPage, scoap3ArticlesPage, ovidJournalPage, smfPage, emsPage, sageMethodsPage, iceGeotechniquePage, jovePage, tairGenePage, opticaPage, crcHandbookDocumentsPage, amsBooksPage, bloomsburyPage, medonePage, ldcCatalogPage} from './publisher_page_readers.mjs';
import {digitalFangzhiSearch} from './digital_fangzhi_browser.mjs';
import {historicNewspaperSearch} from './historic_newspaper_browser.mjs';
import {ftzSearch} from './ftz_browser.mjs';
import {beltroadSearch} from './beltroad_browser.mjs';
import {crggSearch} from './crgg_browser.mjs';
import {cxstarSearch} from './cxstar_browser.mjs';
import {zhangyueSearch} from './zhangyue_browser.mjs';
import {tianluSearch} from './tianlu_browser.mjs';
import {scienceBookSearch} from './sciencebook_browser.mjs';
import {sannongWikiSearch} from './sannong_wiki_browser.mjs';
import {guangzhouDadianSearch} from './guangzhou_dadian_browser.mjs';
import {termonlineSearch} from './termonline_browser.mjs';
import {shidianSearch} from './shidian_browser.mjs';
import {gujidhSearch} from './gujidh_browser.mjs';
import {minguoBookSearch} from './minguo_browser.mjs';
import {cadalManuscriptSearch} from './cadal_manuscripts_browser.mjs';
import {dingxiuSearch} from './dingxiu_browser.mjs';
import {ancientMapSearch} from './ancient_map_browser.mjs';
import {wenquanSearch} from './wenquan_browser.mjs';
import {overseasHanSearch} from './overseas_han_browser.mjs';
import {searchErShiWuShi} from './ershiwushi-session.mjs';
import {aiLiteracySearch} from './ailiteracy_browser.mjs';
import {gpdSearch} from './gpd_browser.mjs';
import {pharmacodiaSearch} from './pharmacodia_browser.mjs';
import {zjuTeachingSearch} from './zju_teaching_browser.mjs';
import {frontierHistorySearch} from './frontier_history_browser.mjs';
import {sunwayReportSearch} from './sunway_report_browser.mjs';
import {itextSearch} from './itext_browser.mjs';
import {theoryResourcesSearch} from './theory_resources_browser.mjs';
import {ejournalFinderSearch} from './ejournal_finder_browser.mjs';
import {bingoSearch} from './bingo_browser.mjs';
import {kukeSearch} from './kuke_browser.mjs';
import {iResearchSearch} from './iresearch_browser.mjs';
import {drcTradeChinaMonthly} from './drc_trade_browser.mjs';
import {htCasesSearch} from './htcases_browser.mjs';
import {hbnReadCurrentTable} from './hbn_browser.mjs';
import {cadalChiangSearch} from './cadal_chiang_browser.mjs';
import {peopleDailySearch} from './people_daily_browser.mjs';
import {nmrdataSearch} from './nmrdata_browser.mjs';
import {koolearnSearch} from './koolearn_browser.mjs';
import {jdReadSearch} from './jdread_browser.mjs';
import {shudiSearch} from './shudi_browser.mjs';
import {infoLiteracySearch} from './infoliteracy_browser.mjs';
import {yiigleSearch} from './yiigle_browser.mjs';
import {opticsJournalSearch} from './opticsjournal_browser.mjs';
import {inscriptionsSearch} from './shutongwen_inscriptions_browser.mjs';
import {shutongwenQslSearch} from './shutongwen_browser.mjs';
import {modernHistorySearch} from './modernhistory_browser.mjs';
import {twsSearch} from './tws_browser.mjs';
import {longyuanMagazineSearch} from './longyuan_browser.mjs';
import {qiyanSearch, qiyanTableInfo} from './qiyan_browser.mjs';
import {searchCNBKSY} from './cnbksy-session.mjs';
import {inindexSearch} from './inindex_browser.mjs';
import {drcnetSearch} from './drcnet_browser.mjs';
import {airitiSearch} from './airiti_browser.mjs';
import {pishuSearch} from './pishu_browser.mjs';
import {pkulawSearch} from './pkulaw_browser.mjs';
import {searchWenshu} from './wenshu-browser.mjs';
const sources = {jstor_institution:searchJstorInstitution,jstor_institution_detail:jstorInstitutionDetail,igpublish_institution:searchIgInstitution,duxiu_book_detail:duxiuBookDetail,aspen_purchased_next:aspenPurchasedNextResponse,gongyuan_images_page:gongyuanImagePage,scopus_author:scopusAuthorResponse,duxiu_books_page:duxiuBooksPage,scopus_detail:scopusDetailResponse,ebsco_mixed_page:ebscoMixedPage,chaoxing_journals_next:chaoxingJournalsNext,longyuan_magazine_page:longyuanMagazinePage,airiti_thesis_page:airitiThesisPage,cadal_search_page:cadalSearchPage,sciencedirect_search_page:scienceDirectSearchPage,sciencedirect_series_page:scienceDirectSeriesPage,inindex_literature_page:inindexLiteraturePageResponse,inindex_literature:inindexLiteratureResponse,scopus_page:scopusPageResponse,inindex_office:inindexOfficeResponse,inindex_toponym:inindexToponymResponse,inindex_person_preview:inindexPersonPreview,watsci_issue:watsciIssue,ieee_institution:ieeeInstitutionSearch,iop_books:iopBooksSearch,kluwer_law_public:kluwerLawJournalSearch,uptodate:upToDateSearch,beck_institution:beckInstitutionSearch,anatomy_foot:anatomyFootSearch,anatomy_knee:anatomyKneeSearch,anatomy_hip:anatomyHipSearch,anatomy_pelvis:anatomyPelvisSearch,anatomy_hand:anatomyHandSearch,anatomy_shoulder:anatomyShoulderSearch,anatomy_thorax:anatomyThoraxSearch,anatomy_spine:anatomySpineSearch,anatomy_head_neck:anatomyHeadNeckSearch,dongfang_catalog:dongfangCatalogResponse,hbn_search:hbnSearchResponse,gongyuan_images:gongyuanImageSearch,fsta_response:fstaSearchResponse,yuedan:yuedanSearch,ebsco_nursing_response:ebscoNursingResponse,dynamed_search_response:dynamedSearchResponse,lexis_cases:lexisCasesPage,hathitrust_bib:hathiBib,ebsco_medline:ebscoMedlineSearch,ebsco_european_americas:ebscoEuropeanAmericasSearch,rup_rss:rupRss,jama_rss:jamaRss,emerald_sru:emeraldSruSearch,wiley_sru:wileySruSearch,zju_tech_experts:zjuTechnologyExpertRecommend,westlaw_cases:westlawCasesSearch,chant:chantSearch,firstsearch_worldcat:firstSearchResults,merck_index:merckIndexResults,degruyter_math_next:degruyterMathNext,diaolong_catalog:diaolongCatalog,scival_institution_summary:scivalInstitutionSummary,reaxys_preview:reaxysDocumentsPreview,sklib_next:sklibNext,cnki_image_detail:cnkiImageDetail,sklib:sklibSearch,cnki_image_page:cnkiImageSearch,investment_claims_page:investmentClaimsPage,calis_journals_next_response:calisJournalsNextResponse,investment_claims_public:investmentClaimsSearch,orbis_apac_quick_response:orbisApacQuickResponse,calis_journals_response:calisJournalsResponse,shudi_books_next_response:shudiBooksNextResponse,minguo_books_next_response:minguoBooksNextResponse,rdfybk_detail:rdfybkDetail,rdfybk_next_response:rdfybkNextResponse,shidian_books_next_response:shidianBooksNextResponse,guangzhou_dadian_next_response:guangzhouDadianNextResponse,cxstar_book_detail:cxstarBookDetail,cxstar_next_response:cxstarNextResponse,tianlu_next_response:tianluNextResponse,theory_resources_next_response:theoryResourcesNextResponse,dingxiu_next_response:dingxiuNextResponse,crgg_country_data_response:crggCountryDataResponse,crgg_next_response:crggNextResponse,overseas_han_next_response:overseasHanNextResponse,inindex_next_response:inindexNextResponse,gpd_selection_next_response:gpdSelectionNextResponse,sunway_report_next_response:sunwayReportNextResponse,digital_fangzhi_detail:digitalFangzhiDetail,digital_fangzhi_next:digitalFangzhiNext,ovid_medline_page:ovidMedlinePage,jus_mundi_paged:jusMundiPaged,ovid_cab_page:ovidCabPage,esi_fields_response:esiFieldsResponse,jcr_profile_response:jcrProfileResponse,esi_fields_page:esiResearchFieldsPage,degruyter_math_journals:degruyterMathJournals,jilin_normative_response:jilinNormativeResponse,incites_organization_filter_response:incitesOrganizationFilterResponse,jiangsu_law_search_response:jiangsuLawSearchResponse,incites_organizations_response:incitesOrganizationsResponse,guangzhou_dadian_response:guangzhouDadianResponse,zhangyue_response:zhangyueResponse,crgg_response:crggResponse,cxstar_response:cxstarResponse,dingxiu_response:dingxiuResponse,tianlu_response:tianluResponse,overseas_han_response:overseasHanResponse,historic_news_response:historicNewsResponse,shidian_books_response:shidianBooksResponse,minguo_books_response:minguoBooksResponse,inindex_response:inindexResponse,osiris_response:osirisResponse,zhejiang_science_reports_response:zhejiangScienceReportsResponse,longyuan_articles_response:longyuanArticlesResponse,shanghai_science_reports_response:shanghaiScienceReportsResponse,longyuan_books_response:longyuanBookResponse,longyuan_magazine_response:longyuanMagazineResponse,cnbksy_response:cnbksyResponse,rdfybk_response:rdfybkResponse,ncpssd_response:ncpssdResponse,cadal_poster_response:cadalPosterResponse,cadal_historical_photos_response:cadalHistoricalPhotosResponse,shudi_books_response:shudiBooksResponse,cadal_inscriptions_response:cadalInscriptionsResponse,theory_resources_response:theoryResourcesResponse,cadal_antique_maps_response:cadalAntiqueMapsResponse,digital_fangzhi_response:digitalFangzhiResponse,cadal_wartime_response:cadalWartimeResponse,cadal_chiang_response:cadalChiangResponse,wanfang_periodical_page2:wanfangPeriodicalPage2Response,wanfang_video_response:wanfangVideoResponse,wanfang_fangzhi_item_response:wanfangFangzhiItemResponse,wanfang_fangzhi_response:wanfangFangzhiResponse,wanfang_magazine:wanfangMagazineResponse,wanfang_nstr:wanfangNstrResponse,wanfang_cstad:wanfangCstadResponse,wanfang_conference:wanfangConferenceResponse,wanfang_periodical:wanfangPeriodicalResponse,wanfang_thesis:wanfangThesisResponse,wanfang_law:wanfangLawResponse,wanfang_standards:wanfangStandardResponse,wanfang_patents:wanfangPatentResponse,wanfang:wanfangSearch,wanfangvideo:wanfangVideoSearch,fangzhi:wanfangFangzhiSearch,ovid_lww_books:ovidLwwBooksCurrent,ovid_biosis:ovidBiosisSearch,ovid_medline:ovidMedlineSearch,ovid_cab:ovidCabSearch,ovid:ovidJournalPage,airiti_ebooks_response:airitiEbooksResponse,zhizhen_conference_response:zhizhenConferenceResponse,zhizhen_law_response:zhizhenLawResponse,zhizhen_newspaper_response:zhizhenNewspaperResponse,thieme_search_response:thiemeSearchResponse,zhizhen_thesis_response:zhizhenThesisResponse,duxiu_books_response:duxiuBooksResponse,cadal_taiwan_resistance:cadalTaiwanResistanceResponse,cadal_manuscript_response:cadalManuscriptResponse,dengke_response:dengkeResponse,pishu_publishdate:pishuPublishDateResponse,airiti_thesis_response:airitiThesisResponse,chaoxing_books_page1:chaoxingBooksPage1Response,chaoxingBooksPage1Response,chaoxing_books_page2:chaoxingBooksPage2Response,cqvip_page1:cqvipPage1Response,cqvip_page2:cqvipPage2Response,gpd_response:gpdSelectionResponse,sunway_reports_response:sunwayReportResponse,aspen_purchased:aspenPurchasedResponse,oreilly_books:oreillyBooksResponse,compendex:compendexResponse,scopus_session:scopusSessionResponse,taylor_books:taylorBooksResponse,wisers:wisersResponse,cnki_citation:cnkiCitationResponse,cnki_culture_journals:cnkiCultureJournalsResponse,cnki_yearbooks:cnkiYearbooksResponse,cnki_reference:cnkiReferenceResponse,cnki_party_journals:cnkiPartyJournalsResponse,cnki_gazette:cnkiGazetteResponse,cnki_serials:cnkiSerialsResponse,cnki_international_conference:cnkiInternationalConferenceResponse,cnki_domestic_conference:cnkiDomesticConferenceResponse,cnki_newspapers:cnkiNewspapersResponse,cnki_journals_zh:cnkiJournalsResponse,cnki_masters:cnkiDegreeSearchResponse,cnki_doctoral:cnkiDegreeSearchResponse,cairn:searchCairnResponse,gale_scholar_lab:galeScholarLabSearch,ebsco_eclassics:searchEbscoEClassics,mathscinet:searchMathSciNet,fanyan:fanyanProjectPage,cnrds:searchCNRDS,zhilin:zhilinPolicyResponse,csmar:searchCSMAR,chaoxing_journals:chaoxingJournalsSearch, wenxinge:wenxingeSearch, cnpe_brill_subscribed:cnpeBrillSubscribedCurrent,  springer_protocols:springerProtocolsCurrent, springer_jetp:springerJetpSearch, rapido:rapidoSearch, adis_drugs:adisDrugsSearch, embase:embaseCurrentResults, itext_wiley:itextWileyBrowse, itext_crc:itextCrcBrowse, cnki_statistical_books:cnkiStatisticalBooksSearch, shutongwen_qhd:shutongwenQhdSearch, shutongwen_stone:shutongwenStoneSearch, calis_yidu:calisYiduSearch, calis_journals:calisJournalsSearch, cnki:cnkiSearch, pqdt_china:pqdtChinaSearch, cochrane_reviews:cochraneReviewsSearch, emerald_books:emeraldBooksSearch, sciencedirect_series:scienceDirectSeriesSearch, sciencedirect_books:scienceDirectBooksSearch, ulrichs:ulrichsSearch, iop:iopSearch, orbis_ma:orbisMaQuickSearch, orbis_americas:orbisAmericasQuickSearch, bankfocus:bankfocusQuickSearch, aps:apsPage, jus_mundi:jusMundiPage, max_planck_law:maxPlanckInternationalLawPage, oxford_reports:oxfordReportsPage, oed_dictionary:oedDictionaryPage, mrs_advances:mrsAdvancesPage, proquest_pqdt:proquestPqdtSearch, proquest_market_research:proquestMarketResearchSearch,    iglibrary_siam:iglibrarySiamSearch, iglibrary_morgan:iglibraryMorganSearch, iglibrary_astm:iglibraryAstmSearch, iglibrary_iec:iglibraryIecSearch, gale_directory:galeDirectorySearch, proquest_eebo:proquestEeboSearch, gale_litfinder:galeLitfinderSearch, gale_criticism:galeCriticismSearch, gale_times:galeTimesSearch, gale_opposing:galeOpposingSearch, gale_business:galeBusinessSearch, gale_ecco:galeEccoSearch, gale_literature:galeLiteratureSearch, gale_world_history:galeWorldHistorySearch, proquest_abi_global:proquestAbiGlobalSearch, proquest_abi_dateline:proquestAbiDatelineSearch, proquest_abi_trade:proquestAbiTradeSearch, proquest_business_research:proquestBusinessResearchSearch, proquest_pharma_news:proquestPharmaNewsSearch, proquest_health_research:proquestHealthResearchSearch, proquest_health:proquestHealthSearch, proquest_pao:proquestPaoSearch, proquest_abi:proquestAbiSearch, proquest_research_library:proquestResearchLibrarySearch, ebsco_newspaper:ebscoNewspaperSearch, ebsco_regional_business:ebscoRegionalBusinessSearch, ebsco_mla_directory:ebscoMlaDirectorySearch, ebsco_mathscinet:ebscoMathscinetSearch, ebsco_environment:ebscoEnvironmentSearch, ebsco_teacher_reference:ebscoTeacherReferenceSearch, ebsco_eric:ebscoEricSearch, ebsco_greenfile:ebscoGreenfileSearch, ebsco_lista:ebscoListaSearch, ebsco_dissertations:ebscoDissertationsSearch, ebsco_ebooks:ebscoEbooksSearch, ebsco_medline_complete:ebscoMedlineCompleteSearch, ebsco_dentistry:ebscoDentistrySearch, ebsco_hospitality:ebscoHospitalitySearch, ebsco_mla:ebscoMlaSearch, ebsco_food:ebscoFoodSearch, ebsco_cinahl:ebscoCinahlSearch, ebsco_academic_premier:ebscoAcademicPremierSearch, ebsco_business_premier:ebscoBusinessPremierSearch, ebsco_communication:ebscoCommunicationSearch, ebsco_psycinfo:ebscoPsycInfoSearch, ebsco_econlit:ebscoEconlitSearch, ebsco_political:ebscoPoliticalSearch, ebsco_bri:ebscoBriSearch, ebsco_psycarticles:ebscoPsycarticlesSearch, ebsco_psychology_collection:ebscoPsychologyCollectionSearch, ebsco_bas:ebscoBasSearch, proquest_lion:proquestLionSearch, late_qing_republic_journals:lateQingRepublicJournalsSearch, airiti_thesis:airitiThesisSearch, cnpe_books:cnpeBooksSearch, gujidh_fifth:gujidhFifthSearch, chaoxing_ebooks:chaoxingEbooksSearch, cnpereading:cnpeReadingSearch, qiushi:qiushiSearch, cssci:cssciSearch, zhonghua_classics:zhonghuaClassicsSearch, people_daily:peopleDailySearch, cadal_chiang:cadalChiangSearch, htcases:htCasesSearch, iresearch:iResearchSearch, drc_trade:drcTradeChinaMonthly, bingo:bingoSearch, kuke:kukeSearch, inscriptions:inscriptionsSearch, qinghuidian:shutongwenQhdSearch, ejournal_finder:ejournalFinderSearch, theory_resources:theoryResourcesSearch, frontier_history:frontierHistorySearch, sunway_report:sunwayReportSearch, itext:itextSearch, zju_teaching:zjuTeachingSearch, gpd:gpdSearch, ailiteracy:aiLiteracySearch, medone:medonePage, pharmacodia:pharmacodiaSearch, bloomsbury:bloomsburyPage, nmrdata:nmrdataSearch, koolearn:koolearnSearch, jdread:jdReadSearch, ldc:ldcCatalogPage, wenquan:wenquanSearch,    cqvip:cqvipSearch, ncpssd:ncpssdSearch, rdfybk:rdfybkSearch, duxiu:duxiuBookSearch, springer:springerPage, sciencedirect:sciencePage, muse:musePage, cambridge:cambridgePage, emerald:emeraldPage, annualreviews:annualReviewsPage, euclid:euclidPage,  britannica:britannicaPage, scoap3:scoap3BooksPage, scoap3articles:scoap3ArticlesPage, ems:emsPage, jove:jovePage, amsbooks:amsBooksPage, crc_handbook:crcHandbookDocumentsPage, optica:opticaPage, tair:tairGenePage, icegeotechnique:iceGeotechniquePage, sagemethods:sageMethodsPage, smf:smfPage, hepjournals:hepJournalsPage, bioone:bioonePage, bmj:bmjPage, sage:sagePage, nature:naturePage, ebookcentral:ebookCentralPage, histories:searchErShiWuShi, ancientmap:ancientMapSearch, overseas_han:overseasHanSearch, crgg:crggSearch, cxstar:cxstarSearch, zhangyue:zhangyueSearch, tianlu:tianluSearch, sciencebook:scienceBookSearch, dingxiu:dingxiuSearch, historicnewspaper:historicNewspaperSearch, ftz:ftzSearch, beltroad:beltroadSearch, sannongwiki:sannongWikiSearch, guangzhoudadian:guangzhouDadianSearch, termonline:termonlineSearch, shidian:shidianSearch, gujidh:gujidhSearch, minguo:minguoBookSearch, cadalmanuscript:cadalManuscriptSearch, shudi:shudiSearch, infoliteracy:infoLiteracySearch, digitalfangzhi:digitalFangzhiSearch, yiigle:yiigleSearch, opticsjournal:opticsJournalSearch, shutongwen:shutongwenQslSearch, modernhistory:modernHistorySearch, tws:twsSearch, longyuan:longyuanMagazineSearch, qiyan:qiyanSearch, cnbksy:searchCNBKSY, inindex:inindexSearch, drcnet:drcnetSearch, airiti:airitiSearch, pishu:pishuSearch, pkulaw:pkulawSearch, wenshu:searchWenshu};
Object.assign(sources,{qingta_menu:qingtaMenu,qingta_statistics:qingtaStatistics});
export function listSources(){return Object.keys(sources);}
export async function search(source,tab,keyword,options={}){
 if(source==='qingta_menu')return qingtaMenu(tab,keyword,options.submitSearch);
 if(source==='qingta_statistics')return qingtaStatistics(tab,keyword,options.submitSearch);
 if(source === 'hathitrust_bib') return hathiBib(tab, options.type ?? 'oclc', keyword);
 if(!Object.hasOwn(sources,source)) throw Error('未知来源；调用 listSources() 查看可用来源');
 if(source === 'watsci_issue') return watsciIssue(tab, options.submitSearch, options.limit ?? 10);
 if(source === 'inindex_literature_page') return inindexLiteraturePageResponse(tab, keyword, options.page, options.submitSearch);
 if(source === 'inindex_literature') return inindexLiteratureResponse(tab, keyword, options.submitSearch);
 if(source === 'inindex_office') return inindexOfficeResponse(tab, keyword, options.submitSearch);
 if(source === 'inindex_toponym') return inindexToponymResponse(tab, keyword, options.submitSearch);
 if(source === 'inindex_person_preview') return inindexPersonPreview(tab, keyword, options.limit ?? 5);
 if(source === 'sciencedirect_search_page') return scienceDirectSearchPage(tab, keyword, options.page, options.submitSearch);
 if(source === 'sciencedirect_series_page') return scienceDirectSeriesPage(tab, options.page, options.submitSearch);
 if(source === 'chaoxing_journals_next') return chaoxingJournalsNext(tab, keyword, options.submitSearch);
 if(source === 'aspen_purchased_next') return aspenPurchasedNextResponse(tab, options.submitSearch);
 if(source === 'longyuan_magazine_page') return longyuanMagazinePage(tab, keyword, options.page, options.submitSearch);
 if(source === 'ebsco_mixed_page') return ebscoMixedPage(tab, keyword, options.page, options.submitSearch);
 if(source === 'jstor_institution') return searchJstorInstitution(tab,keyword,options.page ?? 1);
 if(source === 'jstor_institution_detail') return jstorInstitutionDetail(tab,options.record);
 if(source === 'igpublish_institution') return searchIgInstitution(tab, keyword, options.page ?? 1);
 if(source === 'duxiu_books_page') return duxiuBooksPage(tab, keyword, options.page, options.submitSearch);
 if(source === 'airiti_thesis_page') return airitiThesisPage(tab, keyword, options.page, options.submitSearch);
 if(source === 'cadal_search_page') return cadalSearchPage(tab, keyword, options.page, options.submitSearch);
 if(source === 'scopus_author') return scopusAuthorResponse(tab, keyword, options.first, options.submitSearch);
 if(source === 'scopus_detail') return scopusDetailResponse(tab, keyword, options.submitSearch);
 if(source === 'scopus_page') return scopusPageResponse(tab, keyword, options.page, options.submitSearch);
 if(source === 'ieee_institution') return ieeeInstitutionSearch(tab, keyword, options.submitSearch, options.limit ?? 3);
 if(source === 'iop_books') return iopBooksSearch(tab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'kluwer_law_public') return kluwerLawJournalSearch(tab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'uptodate') return upToDateSearch(tab, keyword, options.submitSearch, options.limit ?? 3);
 if(source === 'beck_institution') return beckInstitutionSearch(tab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'anatomy_foot') return anatomyFootSearch(tab, options.productTab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'anatomy_knee') return anatomyKneeSearch(tab, options.productTab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'anatomy_hip') return anatomyHipSearch(tab, options.productTab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'anatomy_pelvis') return anatomyPelvisSearch(tab, options.productTab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'anatomy_hand') return anatomyHandSearch(tab, options.productTab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'anatomy_shoulder') return anatomyShoulderSearch(tab, options.productTab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'anatomy_thorax') return anatomyThoraxSearch(tab, options.productTab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'anatomy_spine') return anatomySpineSearch(tab, options.productTab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'anatomy_head_neck') return anatomyHeadNeckSearch(tab, options.productTab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'dongfang_catalog') return dongfangCatalogResponse(tab, keyword, options.submitSearch);
 if(source === 'hbn_search') return hbnSearchResponse(tab, keyword, options.submitSearch, options.limit ?? 3);
 if(source === 'gongyuan_images_page') return gongyuanImagePage(tab, keyword, {page:options.page,submitSearch:options.submitSearch,limit:options.limit ?? 3});
 if(source === 'gongyuan_images') return gongyuanImageSearch(tab, keyword, options.submitSearch, options.limit ?? 3);
 if(source === 'fsta_response') return fstaSearchResponse(tab, keyword, options.submitSearch, options.limit ?? 3, options.displayQuery);
 if(source === 'yuedan') return yuedanSearch(tab, keyword, options.submitSearch, options.limit ?? 3);
 if(source === 'ebsco_nursing_response') return ebscoNursingResponse(tab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'dynamed_search_response') return dynamedSearchResponse(tab, keyword, options.submitSearch, options.limit ?? 5);
 if(source === 'ebsco_medline') return ebscoMedlineSearch(tab, keyword);
 if(source === 'ebsco_european_americas') return ebscoEuropeanAmericasSearch(tab, keyword);
 if(source === 'rup_rss') return rupRss(tab, options.feed ?? 'jcb', keyword ?? '', options.limit ?? 10);
 if(source === 'jama_rss') return jamaRss(tab, options.feed ?? 'jama_current', keyword ?? '', options.limit ?? 10);
 if(source === 'emerald_sru') return emeraldSruSearch(tab, keyword, options.page ?? 1, options.pageSize ?? 5);
 if(source === 'wiley_sru') return wileySruSearch(tab, keyword, options.page ?? 1, options.pageSize ?? 5);
 if(source === 'zju_tech_experts') return zjuTechnologyExpertRecommend(tab, keyword, options.limit ?? 3);
 if(source === 'westlaw_cases') return westlawCasesSearch(tab, keyword, options.limit ?? 3);
 if(source === 'chant') return chantSearch(tab, keyword, options.limit ?? 5);
 if(source === 'firstsearch_worldcat') return firstSearchResults(tab);
 if(source === 'merck_index') return merckIndexResults(tab, keyword);
 if(source === 'degruyter_math_next') return degruyterMathNext(tab, keyword);
 if(source === 'diaolong_catalog') return diaolongCatalog(tab);
 if(source === 'scival_institution_summary') return scivalInstitutionSummary(tab);
 if(source === 'reaxys_preview') return reaxysDocumentsPreview(tab, keyword);
 if(source === 'sklib_next') return sklibNext(tab);
 if(source === 'cnki_image_detail') return cnkiImageDetail(tab);
 if(source === 'sklib') return sklibSearch(tab, keyword);
 if(source === 'investment_claims_page') return investmentClaimsPage(tab, keyword, options.page ?? 1);
 if(source === 'orbis_apac_quick_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要正常输入的页面回调');
  return orbisApacQuickResponse(tab, keyword, options.submitSearch);
 }
 if(source === 'calis_journals_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要提供正常页面检索回调');
  return calisJournalsResponse(tab, keyword, options.submitSearch);
 }
 if(source === 'shidian_books_next_response') return shidianBooksNextResponse(tab, keyword, options.page);
 if(source === 'dingxiu_next_response') {
  if(typeof options.clickNext !== 'function') throw Error('需要正常点击下一页的回调');
  return dingxiuNextResponse(tab, keyword, options.clickNext);
 }
 if(source === 'crgg_country_data_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要提供国家筛选的正常页面回调');
  return crggCountryDataResponse(tab, keyword, options.country, options.submitSearch);
 }
 if(source === 'ovid_medline_page') return ovidMedlinePage(tab, keyword, options.start ?? 1);
 if(source === 'jus_mundi_paged') return jusMundiPaged(tab, keyword, options.page ?? 1);
 if(source === 'ovid_cab_page') return ovidCabPage(tab, keyword, options.start ?? 1);
 if(source === 'esi_fields_response') {
  if(typeof options.submitRefresh !== 'function') throw Error('需要提供当前页面的正常刷新回调');
  return esiFieldsResponse(tab, keyword, options.submitRefresh);
 }
 if(source === 'jcr_profile_response') {
  if(typeof options.submitRefresh !== 'function') throw Error('需要提供当前页面的正常刷新回调');
  return jcrProfileResponse(tab, keyword, options.year, options.submitRefresh);
 }
 if(source === "wanfang") return wanfangSearch(tab,keyword,options.page ?? 1,options.category ?? "paper");
 if(source === "wanfangvideo") return wanfangVideoSearch(tab,keyword,options.page ?? 1);
 if(source === 'cnki_journals_zh') {
  if(typeof options.submitSearch === 'function') return cnkiJournalsResponse(tab,keyword,options.submitSearch);
  return searchCnkiJournals(tab,keyword,options.page ?? 1);
 }
 if(source === 'cnki_newspapers') {
  if(typeof options.submitSearch === 'function') return cnkiNewspapersResponse(tab,keyword,options.submitSearch);
  return searchCnkiNewspapers(tab,keyword,options.page ?? 1);
 }
 if(source === 'cnki_domestic_conference') {
  if(typeof options.submitSearch === 'function') return cnkiDomesticConferenceResponse(tab,keyword,options.submitSearch);
  return searchCnkiDomesticConference(tab,keyword,options.page ?? 1);
 }
 if(source === 'cnki_international_conference') {
  if(typeof options.submitSearch === 'function') return cnkiInternationalConferenceResponse(tab,keyword,options.submitSearch);
  return searchCnkiInternationalConference(tab,keyword,options.page ?? 1);
 }
 if(source === 'cnki_serials') {
  if(typeof options.submitSearch === 'function') return cnkiSerialsResponse(tab,keyword,options.submitSearch);
  return searchCnkiSerials(tab,keyword,options.page ?? 1);
 }
 if(source === 'cnki_gazette') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 CNKI政报公报响应接口说明.md');
  return cnkiGazetteResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cnki_party_journals') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 CNKI党建期刊响应接口说明.md');
  return cnkiPartyJournalsResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_nstr') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 万方科技报告响应接口说明.md');
  return wanfangNstrResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'airiti_ebooks_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要从其他分类正常切换电子图书的回调');
  return airitiEbooksResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'zhizhen_conference_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供正常会议论文分类检索的回调');
  return zhizhenConferenceResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'zhizhen_law_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供正常法律法规分类检索的回调');
  return zhizhenLawResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'zhizhen_newspaper_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供正常报纸分类检索的回调');
  return zhizhenNewspaperResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'thieme_search_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供正常检索回调');
  return thiemeSearchResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'zhizhen_thesis_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供正常学位论文检索回调');
  return zhizhenThesisResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'duxiu_book_detail') return duxiuBookDetail(tab,keyword);
 if(source === 'duxiu_books_response') {
  if(typeof options.submitSearch === 'function') return duxiuBooksResponse(tab,keyword,options.submitSearch);
  return searchDuxiuBooks(tab,keyword,options.page ?? 1);
 }
 if(source === 'cadal_taiwan_resistance') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供正常搜本库的回调');
  return cadalTaiwanResistanceResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cadal_manuscript_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供正常搜本库的回调');
  return cadalManuscriptResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'zhejiang_science_reports_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常检索回调');
  return zhejiangScienceReportsResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'longyuan_articles_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常文库检索回调');
  return longyuanArticlesResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'shanghai_science_reports_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常检索回调');
  return shanghaiScienceReportsResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'longyuan_books_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常图书检索回调');
  return longyuanBookResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'longyuan_magazine_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常检索回调');
  return longyuanMagazineResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cnbksy_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常检索回调');
  return cnbksyResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'rdfybk_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常检索回调');
  return rdfybkResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'incites_organization_filter_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要普通机构筛选回调及 startYear/endYear');
  return incitesOrganizationFilterResponse(tab,keyword,options.startYear,options.endYear,options.submitSearch);
 }
 if(source === 'jilin_normative_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常搜索回调');
  return jilinNormativeResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'jiangsu_law_search_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常搜索回调');
  return jiangsuLawSearchResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'incites_organizations_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要普通页面重载回调及 startYear/endYear');
  return incitesOrganizationsResponse(tab,options.startYear,options.endYear,options.submitSearch);
 }
 if(source === 'guangzhou_dadian_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面普通书目检索回调');
  return guangzhouDadianResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'zhangyue_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要频道普通搜索回调');
  return zhangyueResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'crgg_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常资源检索回调');
  return crggResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cxstar_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面普通检索回调');
  return cxstarResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'dingxiu_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要从首页发起普通检索的回调');
  return dingxiuResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'tianlu_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面一般检索回调');
  return tianluResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'overseas_han_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常书目检索回调');
  return overseasHanResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'historic_news_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要选择近代报纸专库并提供正常检索回调');
  return historicNewsResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'shidian_books_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常书籍检索回调');
  return shidianBooksResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'minguo_books_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常标题检索并打开图书结果的回调');
  return minguoBooksResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'inindex_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面普通姓名检索回调');
  return inindexResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'osiris_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面普通搜索确认回调');
  return osirisResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'ncpssd_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常搜索回调');
  return ncpssdResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cadal_poster_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要特藏首页正常搜本库的回调');
  return cadalPosterResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cadal_historical_photos_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要特藏首页正常搜本库的回调');
  return cadalHistoricalPhotosResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'shudi_books_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常检索回调');
  return shudiBooksResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cadal_inscriptions_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要特藏首页正常搜本库的回调');
  return cadalInscriptionsResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'theory_resources_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常检索回调');
  return theoryResourcesResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cadal_antique_maps_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要特藏首页正常搜本库的回调');
  return cadalAntiqueMapsResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'digital_fangzhi_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要页面正常检索回调');
  return digitalFangzhiResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cadal_wartime_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要正常搜本库的回调');
  return cadalWartimeResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cadal_chiang_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要正常搜本库的回调');
  return cadalChiangResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_periodical_page2') {
  if(typeof options.submitSearch !== 'function') throw Error('需要从首屏正常点击第二页的回调');
  return wanfangPeriodicalPage2Response(tab,keyword,options.submitSearch);
 }
 if(source === 'dengke_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供页面正常姓名检索的回调');
  return dengkeResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_video_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供页面正常检索视频的回调');
  return wanfangVideoResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'pishu_publishdate') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供页面按出版时间排序的回调');
  return pishuPublishDateResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_fangzhi_item_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供页面正常检索条目的回调');
  return wanfangFangzhiItemResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_fangzhi_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调');
  return wanfangFangzhiResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'airiti_thesis_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供页面从期刊切换至学位论文的回调');
  return airitiThesisResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_magazine') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 万方期刊目录响应接口说明.md');
  return wanfangMagazineResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'chaoxing_books_page1') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面正常返回首页的回调；参见 超星电子书首页响应接口说明.md');
  return chaoxingBooksPage1Response(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_cstad') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 万方科技成果响应接口说明.md');
  return wanfangCstadResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'chaoxing_books_page2') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面正常翻到第二页的回调；参见 超星电子书第二页响应接口说明.md');
  return chaoxingBooksPage2Response(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_conference') {
  if(typeof options.submitSearch === 'function') return wanfangConferenceResponse(tab,keyword,options.submitSearch);
  return searchWanfangConference(tab,keyword,options.page ?? 1);
 }
 if(source === 'wanfang_periodical') {
  if(typeof options.submitSearch === 'function') return wanfangPeriodicalResponse(tab,keyword,options.submitSearch);
  return searchWanfangPeriodical(tab,keyword,options.page ?? 1);
 }
 if(source === 'cqvip_page1') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面正常返回第一页的回调；参见 维普期刊首页响应接口说明.md');
  return cqvipPage1Response(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_thesis') {
  if(typeof options.submitSearch === 'function') return wanfangThesisResponse(tab,keyword,options.submitSearch);
  return searchWanfangThesis(tab,keyword,options.page ?? 1);
 }
 if(source === 'cqvip_page2') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面正常翻到第二页的回调；参见 维普期刊第二页响应接口说明.md');
  return cqvipPage2Response(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_law') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 万方法规分类响应接口说明.md');
  return wanfangLawResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_standards') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 万方中外标准响应接口说明.md');
  return wanfangStandardResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'gpd_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 尚唯GPD选型响应接口说明.md');
  return gpdSelectionResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'wanfang_patents') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 万方中外专利响应接口说明.md');
  return wanfangPatentResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'sunway_reports_response') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 尚唯科技报告响应接口说明.md');
  return sunwayReportResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'aspen_purchased') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常筛选回调；参见 Aspen已购书目响应接口说明.md');
  return aspenPurchasedResponse(tab,options.submitSearch);
 }
 if(source === 'oreilly_books') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 OReilly机构书目接口说明.md');
  return oreillyBooksResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'compendex') {
  if(typeof options.submitSearch === 'function') return compendexResponse(tab,keyword,options.submitSearch);
  return searchCompendex(tab,keyword,options.page ?? 1);
 }
 if(source === 'scopus_session') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 Scopus机构会话题录接口说明.md');
  return scopusSessionResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'taylor_books') {
  if(typeof options.submitSearch === 'function') return taylorBooksResponse(tab,keyword,options.submitSearch,options.page ?? 1);
  return searchTaylorBooks(tab,keyword,options.page ?? 1);
 }
 if(source === 'wisers') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 慧科新闻搜索接口说明.md');
  return wisersResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cnki_citation') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 CNKI中国引文库响应接口说明.md');
  return cnkiCitationResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cnki_culture_journals') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 CNKI精品文化期刊响应接口说明.md');
  return cnkiCultureJournalsResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cnki_yearbooks') {
  if(typeof options.submitSearch === 'function') return cnkiYearbooksResponse(tab,keyword,options.submitSearch);
  return searchCnkiYearbooks(tab,keyword,options.page ?? 1);
 }
 if(source === 'cnki_reference') {
  if(typeof options.submitSearch !== 'function') throw Error('需要调用者提供当前页面的正常检索回调；参见 CNKI工具书词目响应接口说明.md');
  return cnkiReferenceResponse(tab,keyword,options.submitSearch);
 }
 if(source === 'cnki_doctoral' || source === 'cnki_masters') {
  const degree=source === 'cnki_doctoral' ? '博士' : '硕士';
  if(typeof options.submitSearch === 'function') return cnkiDegreeSearchResponse(tab,keyword,degree,options.submitSearch);
  return searchCnkiDegree(tab,keyword,degree,options.page ?? 1);
 }
 if(source === 'fanyan') {
  if (typeof keyword !== 'string' || !keyword.trim()) throw Error('需要当前搜索关键词');
  const current=await tab.playwright.evaluate(()=>document.querySelector('#guanJianCi1')?.value?.trim()||'');
  if(current!==keyword.trim()) throw Error('请先在泛研搜索对应关键词');
  return fanyanProjectPage(tab,options.page);
 }
 if(source === 'lexis_cases') return lexisCasesPage(tab,keyword,options);
 return sources[source](tab,keyword);
}

export async function readQiyanTable(tab){ return qiyanTableInfo(tab); }

export async function readHbnTable(tab){ return hbnReadCurrentTable(tab); }
